from PyInstaller.utils.hooks import collect_all

# 收集所有 plotly 相关的包
datas, binaries, hiddenimports = collect_all('plotly')
datas += collect_all('dash')[0]
datas += collect_all('open3d')[0]
hiddenimports += [
    'plotly.graph_objs._figure',
    'plotly.graph_objs',
    'dash',
    'dash.dcc',
    'open3d',
    'open3d.visualization',
    'open3d.visualization.draw_plotly'
] 