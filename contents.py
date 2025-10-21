import datetime
import glob
import os
import warnings

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pyecharts import options as opts
from pyecharts.charts import Bar, Line, Pie, Scatter, Page

warnings.filterwarnings('ignore')

# 获取当前时间字符串
current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
print(f"当前时间戳: {current_time}")

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# 创建桌面contents文件夹
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
output_folder = os.path.join(desktop_path, "contents")

# 如果文件夹不存在则创建
if not os.path.exists(output_folder):
    os.makedirs(output_folder)
    print(f"已创建输出文件夹: {output_folder}")
else:
    print(f"输出文件夹已存在: {output_folder}")


# 自动读取CSV文件
def find_latest_creator_contents():
    """查找最新的creator_contents开头的CSV文件"""
    # D:\\MediaCrawler-main\\data
    directory = "D:\\MediaCrawler-main\\data"
    pattern = os.path.join(directory, "creator_contents*.csv")
    csv_files = glob.glob(pattern)

    if not csv_files:
        raise FileNotFoundError(f"在目录 {directory} 中未找到以 'creator_contents' 开头的 CSV 文件")

    # 按修改时间排序，取最新的文件
    csv_files.sort(key=os.path.getmtime, reverse=True)
    latest_file = csv_files[0]
    print(f"找到最新文件: {latest_file}")
    return latest_file


# 读取数据
try:
    csv_file = find_latest_creator_contents()
    df = pd.read_csv(csv_file, encoding='utf-8')
except FileNotFoundError as e:
    print(f"错误: {e}")
    exit(1)
except Exception as e:
    print(f"读取文件时出错: {e}")
    exit(1)

# 获取文件名用于报告输出
csv_filename = os.path.basename(csv_file)

print("数据基本信息:")
print(f"数据集形状: {df.shape}")
print("\n列名:")
print(df.columns.tolist())
print("\n前5行数据:")
print(df.head())

# 数据清洗
columns_to_drop = ['aweme_id', 'user_id', 'sec_uid', 'short_user_id', 'user_unique_id',
                   'aweme_url', 'cover_url', 'video_download_url', 'music_download_url',
                   'note_download_url', 'source_keyword', 'avatar']

df_clean = df.drop(columns=[col for col in columns_to_drop if col in df.columns])

print(f"\n清洗后数据形状: {df_clean.shape}")


# 时间处理函数
def process_timestamps(create_time, last_modify_ts):
    local_time = datetime.datetime.fromtimestamp(create_time)
    local_last_time = datetime.datetime.fromtimestamp(last_modify_ts / 1000)

    time_diff = local_last_time - local_time
    days = time_diff.days
    seconds = time_diff.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    return local_time, local_last_time, days, hours, minutes, seconds


# 应用时间处理
time_data = []
for i, row in df_clean.iterrows():
    create_ts = row['create_time']
    last_modify_ts = row['last_modify_ts']

    if pd.notna(create_ts) and pd.notna(last_modify_ts):
        local_time, local_last_time, days, hours, minutes, seconds = process_timestamps(
            create_ts, last_modify_ts
        )
        time_data.append({
            'create_time_dt': local_time,
            'last_modify_dt': local_last_time,
            'time_diff_days': days,
            'time_diff_hours': hours,
            'time_diff_minutes': minutes
        })
    else:
        time_data.append({
            'create_time_dt': None,
            'last_modify_dt': None,
            'time_diff_days': 0,
            'time_diff_hours': 0,
            'time_diff_minutes': 0
        })

# 添加时间相关列
time_df = pd.DataFrame(time_data)
df_analysis = pd.concat([df_clean.reset_index(drop=True), time_df], axis=1)

# 提取日期信息
df_analysis['create_date'] = df_analysis['create_time_dt'].dt.date
df_analysis['create_hour'] = df_analysis['create_time_dt'].dt.hour
df_analysis['create_weekday'] = df_analysis['create_time_dt'].dt.weekday

print("\n数据处理完成，开始可视化...")

# 1. Seaborn可视化
print("创建Seaborn可视化...")

# 创建子图
fig, axes = plt.subplots(2, 3, figsize=(20, 12))
fig.suptitle('抖音教育内容运营数据分析', fontsize=16, fontweight='bold')

# 1.1 视频类型分布
aweme_type_counts = df_analysis['aweme_type'].value_counts()
sns.barplot(x=aweme_type_counts.index, y=aweme_type_counts.values, ax=axes[0, 0], palette='viridis')
axes[0, 0].set_title('视频类型分布', fontsize=12, fontweight='bold')
axes[0, 0].set_xlabel('视频类型')
axes[0, 0].set_ylabel('数量')
for i, v in enumerate(aweme_type_counts.values):
    axes[0, 0].text(i, v + 0.1, str(v), ha='center', va='bottom')

# 1.2 互动数据分布
interaction_columns = ['liked_count', 'collected_count', 'comment_count', 'share_count']
interaction_data = df_analysis[interaction_columns].sum()

# 创建中文标签映射
interaction_labels = ['喜欢数', '收藏数', '评论数', '分享数']

sns.barplot(x=interaction_labels, y=interaction_data.values, ax=axes[0, 1], palette='Set2')
axes[0, 1].set_title('总互动数据分布', fontsize=12, fontweight='bold')
axes[0, 1].set_xlabel('互动类型')
axes[0, 1].set_ylabel('总数')
for i, v in enumerate(interaction_data.values):
    axes[0, 1].text(i, v + 5, str(int(v)), ha='center', va='bottom')

# 1.3 发布时间分布（小时）
hour_distribution = df_analysis['create_hour'].value_counts().sort_index()
sns.lineplot(x=hour_distribution.index, y=hour_distribution.values, ax=axes[0, 2], marker='o', linewidth=2.5)
axes[0, 2].set_title('发布时间分布（小时）', fontsize=12, fontweight='bold')
axes[0, 2].set_xlabel('小时')
axes[0, 2].set_ylabel('发布数量')
axes[0, 2].grid(True, alpha=0.3)

# 1.4 点赞数与评论数关系
sns.scatterplot(data=df_analysis, x='liked_count', y='comment_count', ax=axes[1, 0], alpha=0.7, s=60)
axes[1, 0].set_title('喜欢数与评论数关系', fontsize=12, fontweight='bold')
axes[1, 0].set_xlabel('喜欢数')
axes[1, 0].set_ylabel('评论数')
axes[1, 0].grid(True, alpha=0.3)

# 1.5 用户发布量分析
user_counts = df_analysis['nickname'].value_counts().head(10)
sns.barplot(y=user_counts.index, x=user_counts.values, ax=axes[1, 1], palette='coolwarm')
axes[1, 1].set_title('TOP10用户发布量', fontsize=12, fontweight='bold')
axes[1, 1].set_xlabel('发布数量')
axes[1, 1].set_ylabel('用户昵称')

# 1.6 时间差分布
time_diff_filtered = df_analysis[df_analysis['time_diff_days'] < 30]['time_diff_days']
sns.histplot(time_diff_filtered, ax=axes[1, 2], bins=15, kde=True, color='skyblue')
axes[1, 2].set_title('内容修改时间差分布（天）', fontsize=12, fontweight='bold')
axes[1, 2].set_xlabel('时间差（天）')
axes[1, 2].set_ylabel('频次')
axes[1, 2].grid(True, alpha=0.3)

plt.tight_layout()

# 保存Seaborn图片到桌面contents文件夹
seaborn_filename = f'seaborn_contents_analysis_{current_time}.png'
seaborn_filepath = os.path.join(output_folder, seaborn_filename)
plt.savefig(seaborn_filepath, dpi=300, bbox_inches='tight')
print(f"Seaborn图表已保存为: {seaborn_filepath}")

# 2. Pyecharts HTML可视化
print("创建Pyecharts HTML可视化...")

# 创建页面
page = Page(layout=Page.SimplePageLayout)

# 2.1 互动数据对比图
interaction_avg = df_analysis[interaction_columns].mean().round(2)

bar_interaction = (
    Bar()
    .add_xaxis(interaction_labels)
    .add_yaxis("平均互动数", interaction_avg.tolist(),
               label_opts=opts.LabelOpts(is_show=True, position="top"))
    .set_global_opts(
        title_opts=opts.TitleOpts(title="平均互动数据对比"),
        xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=0)),
        yaxis_opts=opts.AxisOpts(name="平均数量"),
        legend_opts=opts.LegendOpts(pos_left="center"),
    )
)
page.add(bar_interaction)

# 2.2 发布时间分布图
hour_data = df_analysis['create_hour'].value_counts().sort_index()

line_hour = (
    Line()
    .add_xaxis([f"{int(h)}:00" for h in hour_data.index])
    .add_yaxis(
        "发布数量",
        hour_data.values.tolist(),
        is_smooth=True,
        label_opts=opts.LabelOpts(is_show=False),
        linestyle_opts=opts.LineStyleOpts(width=3),
        symbol="circle",
        symbol_size=8,
    )
    .set_global_opts(
        title_opts=opts.TitleOpts(title="24小时发布趋势"),
        xaxis_opts=opts.AxisOpts(
            name="时间",
            axislabel_opts=opts.LabelOpts(rotate=0)
        ),
        yaxis_opts=opts.AxisOpts(
            name="发布数量",
            min_=0,  # 确保Y轴从0开始
            interval=1  # 设置刻度间隔为1
        ),
        tooltip_opts=opts.TooltipOpts(trigger="axis"),
    )
)
page.add(line_hour)

# 2.3 用户发布量饼图
user_pie_data = df_analysis['nickname'].value_counts().head(8)
pie_user = (
    Pie()
    .add(
        "",
        [list(z) for z in zip(user_pie_data.index.tolist(), user_pie_data.values.tolist())],
        radius=["30%", "75%"],
        center=["50%", "50%"],
        rosetype="radius",
    )
    .set_global_opts(
        title_opts=opts.TitleOpts(title="用户发布量分布"),
        legend_opts=opts.LegendOpts(
            orient="vertical",
            pos_left="left",
            pos_top="middle"
        ),
    )
    .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}"))
)
page.add(pie_user)

# 2.4 视频类型分布
type_pie_data = df_analysis['aweme_type'].value_counts()
pie_type = (
    Pie()
    .add(
        "",
        [list(z) for z in zip([f"类型{str(x)}" for x in type_pie_data.index], type_pie_data.values.tolist())],
        center=["50%", "50%"],
    )
    .set_global_opts(
        title_opts=opts.TitleOpts(title="视频类型分布"),
        legend_opts=opts.LegendOpts(
            orient="vertical",
            pos_right="right",
            pos_top="middle"
        ),
    )
    .set_series_opts(
        label_opts=opts.LabelOpts(formatter="{b}: {c} ({d}%)")
    )
)
page.add(pie_type)

# 2.5 互动数据散点矩阵（喜欢vs收藏）
scatter_interaction = (
    Scatter()
    .add_xaxis(df_analysis['liked_count'].tolist())
    .add_yaxis(
        "喜欢vs收藏",
        df_analysis['collected_count'].tolist(),
        symbol_size=10,
        label_opts=opts.LabelOpts(is_show=False),
    )
    .set_global_opts(
        title_opts=opts.TitleOpts(title="喜欢与收藏关系散点图"),
        xaxis_opts=opts.AxisOpts(name="喜欢数", type_="value"),
        yaxis_opts=opts.AxisOpts(name="收藏数", type_="value"),
        tooltip_opts=opts.TooltipOpts(trigger="item"),
    )
)
page.add(scatter_interaction)

# 2.6 时间序列分析
# 创建完整的日期范围，确保从0开始
date_range = pd.date_range(
    start=df_analysis['create_date'].min(),
    end=df_analysis['create_date'].max(),
    freq='D'
)

# 计算每日发布数量，确保所有日期都有值
date_counts = df_analysis['create_date'].value_counts().reindex(date_range.date, fill_value=0).sort_index()

line_date = (
    Line()
    .add_xaxis([d.strftime('%Y-%m-%d') for d in date_counts.index])
    .add_yaxis(
        "每日发布量",
        date_counts.values.tolist(),
        is_smooth=False,  # 不使用平滑曲线，确保显示实际数据点
        label_opts=opts.LabelOpts(is_show=False),
        linestyle_opts=opts.LineStyleOpts(width=2),
        symbol="circle",
        symbol_size=6,
    )
    .set_global_opts(
        title_opts=opts.TitleOpts(title="每日发布趋势"),
        xaxis_opts=opts.AxisOpts(
            name="日期",
            axislabel_opts=opts.LabelOpts(rotate=0)
        ),
        yaxis_opts=opts.AxisOpts(
            name="发布数量",
            min_=0,  # 确保Y轴从0开始
            interval=1  # 设置刻度间隔为1，确保每次增长1
        ),
        tooltip_opts=opts.TooltipOpts(trigger="axis"),
        datazoom_opts=[opts.DataZoomOpts()],
    )
)
page.add(line_date)

# 保存HTML文件到桌面contents文件夹
html_filename = f"pyecharts_contents_analysis_{current_time}.html"
html_filepath = os.path.join(output_folder, html_filename)
page.render(html_filepath)

print(f"Pyecharts交互图表已保存为: {html_filepath}")

# 3. 生成数据报告
report_filename = f"data_contents_analysis_report_{current_time}.txt"
report_filepath = os.path.join(output_folder, report_filename)
with open(report_filepath, 'w', encoding='utf-8') as f:
    f.write("抖音教育内容运营数据分析报告\n")
    f.write("=" * 50 + "\n")
    f.write(f"生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"数据文件: {csv_filename}\n")
    f.write(f"总记录数: {len(df_analysis)}\n\n")

    f.write("关键指标统计:\n")
    f.write("-" * 30 + "\n")
    f.write(f"用户数量: {df_analysis['nickname'].nunique()}\n")
    f.write(f"视频类型数量: {df_analysis['aweme_type'].nunique()}\n")
    f.write(f"平均喜欢数: {df_analysis['liked_count'].mean():.2f}\n")
    f.write(f"平均收藏数: {df_analysis['collected_count'].mean():.2f}\n")
    f.write(f"平均评论数: {df_analysis['comment_count'].mean():.2f}\n")
    f.write(f"平均分享数: {df_analysis['share_count'].mean():.2f}\n\n")

    f.write("发布趋势分析:\n")
    f.write("-" * 30 + "\n")
    f.write(f"数据时间范围: {df_analysis['create_date'].min()} 至 {df_analysis['create_date'].max()}\n")
    f.write(f"最活跃发布时间段: {hour_data.idxmax()}:00-{hour_data.idxmax() + 1}:00\n")
    f.write(f"该时段发布数量: {hour_data.max()}\n")
    f.write(f"总天数: {len(date_range)}天\n")
    f.write(f"有发布内容的天数: {(date_counts > 0).sum()}天\n")
    f.write(f"平均每日发布量: {date_counts.mean():.2f}个\n\n")

    f.write("用户活跃度TOP5:\n")
    f.write("-" * 30 + "\n")
    top_users = df_analysis['nickname'].value_counts().head()
    for i, (user, count) in enumerate(top_users.items(), 1):
        f.write(f"{i}. {user}: {count}个视频\n")

    f.write(f"\n生成文件:\n")
    f.write("-" * 30 + "\n")
    f.write(f"1. Seaborn静态图表: {seaborn_filename}\n")
    f.write(f"2. Pyecharts交互图表: {html_filename}\n")
    f.write(f"3. 数据报告: {report_filename}\n")
    f.write(f"\n文件位置: {output_folder}\n")

print(f"数据报告已保存为: {report_filepath}")

print("\n数据分析完成!")
print("\n关键发现:")
print(f"1. 总视频数量: {len(df_analysis)}")
print(f"2. 主要用户数量: {df_analysis['nickname'].nunique()}")
print(f"3. 平均喜欢数: {df_analysis['liked_count'].mean():.2f}")
print(f"4. 平均评论数: {df_analysis['comment_count'].mean():.2f}")
print(f"5. 最活跃发布时间段: {hour_data.idxmax()}:00-{hour_data.idxmax() + 1}:00")
print(f"6. 最高互动视频喜欢数: {df_analysis['liked_count'].max()}")
print(f"7. 数据覆盖天数: {len(date_range)}天")

# 生成运营建议
print("\n运营建议:")
print("1. 重点关注高互动时间段进行内容发布")
print("2. 分析高喜欢内容的主题和形式特征")
print("3. 优化评论互动策略，提升用户参与度")
print("4. 跟踪内容修改频率与互动关系")
print("5. 建立用户发布质量评估体系")
print("6. 关注发布频率与内容质量的平衡")

print(f"\n所有文件已生成完成，时间戳: {current_time}")
print(f"文件保存位置: {output_folder}")

"""
主程序入口
"""
if __name__ == "__main__":
    print("程序启动")
