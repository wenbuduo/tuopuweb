# 导入所需的库和模块
from flask import Flask, render_template, request, jsonify, send_file
import copy

# 创建一个Flask应用
app = Flask(__name__)

ALLOWED_EXTENSIONS = {'txt'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# 定义默认路由，用于显示主页
@app.route('/')
def index():
    return render_template('index.html')


# 定义生成关系图的路由
@app.route('/generate', methods=['POST'])
def generate():
    # 从POST请求中获取用户输入的节点数据
    data_input = request.form.get('data_input')

    # 解析用户输入的数据，将其转换为节点和边的形式
    nodes, edges,isvalid = parse_data_input(data_input)

    # 创建关系图数据
    graph_data = create_graph_data(nodes, edges)

    # 计算拓扑排序的结果
    topological_sort_result = topological_sort(nodes, edges)

    # 保存排序结果为txt文件
    save_path = 'static/topological_sort_result.txt'
    with open(save_path, 'w') as f:
        for node in topological_sort_result:
            f.write(node + '\n')

    # 返回数据以JSON格式，包括文件下载链接
    return jsonify(isvalid = isvalid, graph_data=graph_data, topological_sort_result=topological_sort_result, download_link=save_path)


# 辅助函数：解析用户输入的节点数据
def parse_data_input(data_input):
    nodes = set()
    edges = []
    isvalid = True
    for line in data_input.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        if not line.startswith('<') or not line.endswith('>'):
            isvalid = False
            return list(nodes), edges, isvalid
        parts = line.strip('<>').split(',')

        if len(parts) != 2:
            isvalid = False
            return list(nodes), edges,isvalid
        else:
            parent, child = parts[0], parts[1]
            nodes.add(parent)
            nodes.add(child)
            edges.append((parent, child))

    return list(nodes), edges,isvalid


# 辅助函数：创建关系图数据
def create_graph_data(nodes, edges):
    graph_data = {
        'nodes': [{'name': node} for node in nodes],
        'edges': [{'source': edge[0], 'target': edge[1]} for edge in edges],
    }
    return graph_data


# 辅助函数：进行拓扑排序
def topological_sort(nodes, edges):
    graph = {node: [] for node in nodes}
    in_degree = {node: 0 for node in nodes}

    for edge in edges:
        graph[edge[0]].append(edge[1])
        in_degree[edge[1]] += 1

    results = backtrack([], nodes, graph, in_degree)

    final_results = []
    for result in results:
        for ch in result:
            final_results.append(ch)
        final_results.append('---')

    return final_results


def backtrack(current, remaining, graph, in_degree):
    if not remaining:
        return [current]

    results = []
    for node in remaining:
        if in_degree[node] == 0:
            new_current = copy.copy(current)
            new_current.append(node)
            new_remaining = [n for n in remaining if n != node]

            for neighbor in graph[node]:
                in_degree[neighbor] -= 1

            new_results = backtrack(new_current, new_remaining, graph, in_degree)

            for result in new_results:
                results.append(result)

            for neighbor in graph[node]:
                in_degree[neighbor] += 1

    return results


# 对文件进行处理
@app.route('/upload', methods=['POST'])
def upload():
    # 检查是否有文件上传
    if 'data_file' not in request.files:
        return "没有文件上传"

    data_file = request.files['data_file']

    # 检查文件是否为空
    if data_file.filename == '':
        return "请选择一个文件"

    # 检查文件类型是否允许
    if not allowed_file(data_file.filename):
        return "文件类型不允许"

    # 读取文件内容
    data = data_file.read().decode('utf-8')

    nodes, edges,isvalid = parse_data_input(data)

    graph_data = create_graph_data(nodes, edges)

    # 执行拓扑排序
    topological_sort_result = topological_sort(nodes, edges)

    # 保存排序结果为txt文件
    save_path = 'static/topological_sort_result.txt'
    with open(save_path, 'w') as f:
        for node in topological_sort_result:
            f.write(node + '\n')

    # 返回渲染的页面和数据
    return render_template('index.html', graph_data=graph_data, topological_sort_result=topological_sort_result,download_link=save_path)
    # return jsonify(graph_data=graph_data, topological_sort_result=topological_sort_result, download_link=save_path)


# 提供下载排序结果的txt文件
@app.route('/download')
def download():
    return send_file('static/topological_sort_result.txt', as_attachment=True)

# 启动Flask应用
if __name__ == '__main__':
    app.run(debug=True)
