"""
运营数据可视化 Seaborn && PyEcharts 分析
"""
import datetime
import glob
import os
import re
import warnings
from collections import Counter

import jieba
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pyecharts import options as opts
from pyecharts.charts import Bar, Pie, Line, WordCloud, Map, Page
from pyecharts.commons.utils import JsCode
from pyecharts.globals import ThemeType, SymbolType

warnings.filterwarnings('ignore')

# 中文显示问题
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号


def extract_province(location):
    """从IP位置中提取省份信息"""
    if pd.isna(location) or location == '未知':
        return '未知'

    # 中国省份列表
    provinces = [
        '北京', '天津', '上海', '重庆', '河北', '山西', '辽宁', '吉林', '黑龙江',
        '江苏', '浙江', '安徽', '福建', '江西', '山东', '河南', '湖北', '湖南',
        '广东', '海南', '四川', '贵州', '云南', '陕西', '甘肃', '青海', '台湾',
        '内蒙古', '广西', '西藏', '宁夏', '新疆', '香港', '澳门'
    ]

    # 检查是否包含省份名称
    for province in provinces:
        if province in location:
            return province

    # 如果找不到省份，返回原位置
    return location


def extract_keywords(texts, top_n=50):
    """提取关键词"""
    all_words = []
    for text in texts:
        if pd.isna(text):
            continue
        words = jieba.cut(str(text))
        # 过滤短词和停用词
        words = [word for word in words if len(word) > 1 and not word.isspace()]
        all_words.extend(words)

    word_freq = Counter(all_words)
    return word_freq.most_common(top_n)


class CommentDataAnalyzer:
    def __init__(self, file_path):
        self.file_path = file_path
        self.df = None

        # 创建桌面comments文件夹
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        self.output_folder = os.path.join(desktop_path, "comments")

        # 如果文件夹不存在则创建
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
            print(f"已创建输出文件夹: {self.output_folder}")
        else:
            print(f"输出文件夹已存在: {self.output_folder}")

        self.load_data()

    def load_data(self):
        """加载并预处理数据"""
        try:
            # 读取CSV文件
            self.df = pd.read_csv(self.file_path, encoding='utf-8')
            print(f"数据加载成功，共{len(self.df)}条评论")

            # 数据预处理
            self.preprocess_data()

        except Exception as e:
            print(f"数据加载失败: {e}")

    def preprocess_data(self):
        """数据预处理 - 使用向量化操作"""
        print("正在转换时间格式...")

        # 使用datetime转换时间
        self.df['create_time_dt'] = self.df['create_time'].apply(
            lambda x: datetime.datetime.fromtimestamp(x))

        self.df['last_modify_ts_dt'] = self.df['last_modify_ts'].apply(
            lambda x: datetime.datetime.fromtimestamp(x / 1000))

        # 提取日期信息（基于创建时间）
        self.df['date'] = self.df['create_time_dt'].apply(lambda x: x.date())
        self.df['hour'] = self.df['create_time_dt'].apply(lambda x: x.hour)
        self.df['weekday'] = self.df['create_time_dt'].apply(lambda x: x.weekday())

        # 计算评论长度
        self.df['content_length'] = self.df['content'].fillna('').apply(len)

        # 清理IP位置数据 - 提取省份信息
        self.df['ip_location_clean'] = self.df['ip_location'].fillna('未知')
        self.df['province'] = self.df['ip_location_clean'].apply(extract_province)

        # 标记是否包含表情
        self.df['has_emoji'] = self.df['content'].fillna('').apply(
            lambda x: bool(re.search(r'\[.*?]', str(x)))
        )

        # 计算时间差
        def calculate_time_diff(row):
            time_diff = row['last_modify_ts_dt'] - row['create_time_dt']
            days = time_diff.days
            seconds = time_diff.seconds
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60
            return f"{days}天 {hours}小时 {minutes}分钟 {seconds}秒"

        self.df['time_diff_str'] = self.df.apply(calculate_time_diff, axis=1)
        self.df['time_diff_days'] = (self.df['last_modify_ts_dt'] - self.df['create_time_dt']).dt.total_seconds() / (
                24 * 3600)

        # 为可视化添加格式化的时间字符串
        self.df['last_modify_ts_str'] = self.df['last_modify_ts_dt'].apply(
            lambda x: x.strftime("%Y-%m-%d %H:%M:%S"))
        self.df['create_time_str'] = self.df['create_time_dt'].apply(
            lambda x: x.strftime("%Y-%m-%d %H:%M:%S"))

        print("数据预处理完成")

    def analyze_basic_stats(self):
        """基础统计分析"""
        print("\n=== 基础统计 ===")
        print(f"数据时间范围: {self.df['create_time_dt'].min()} 到 {self.df['create_time_dt'].max()}")
        print(f"评论总数: {len(self.df)}")
        print(f"涉及视频数: {self.df['aweme_id'].nunique()}")
        print(f"涉及用户数: {self.df['user_id'].nunique()}")
        print(f"平均评论长度: {self.df['content_length'].mean():.1f}字符")
        print(f"包含表情的评论比例: {self.df['has_emoji'].mean():.2%}")
        print(f"平均点赞数: {self.df['like_count'].mean():.1f}")
        print(f"平均回复数: {self.df['sub_comment_count'].mean():.1f}")
        print(f"平均创建到修改时间差: {self.df['time_diff_days'].mean():.2f}天")

        # 打印省份分布
        province_dist = self.df['province'].value_counts()
        print(f"\n省份分布:")
        for province, count in province_dist.head(10).items():
            print(f"  {province}: {count}条评论")

    def generate_txt_report(self):
        """生成详细的TXT数据报告"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"data_comments_analysis_report_{timestamp}.txt"
        report_filepath = os.path.join(self.output_folder, report_filename)

        print(f"\n正在生成TXT数据报告: {report_filepath}")

        with open(report_filepath, 'w', encoding='utf-8') as f:
            # 报告头部信息
            f.write("=" * 80 + "\n")
            f.write("抖音评论数据综合分析报告\n")
            f.write("=" * 80 + "\n")
            f.write(f"报告生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"数据文件: {self.file_path}\n")
            f.write(f"数据记录总数: {len(self.df)}\n")
            f.write("=" * 80 + "\n\n")

            # 1. 基础统计信息
            f.write("1. 基础统计信息\n")
            f.write("-" * 40 + "\n")
            f.write(f"数据时间范围: {self.df['create_time_dt'].min()} 到 {self.df['create_time_dt'].max()}\n")
            f.write(f"评论总数: {len(self.df)}\n")
            f.write(f"涉及视频数: {self.df['aweme_id'].nunique()}\n")
            f.write(f"涉及用户数: {self.df['user_id'].nunique()}\n")
            f.write(f"平均评论长度: {self.df['content_length'].mean():.1f}字符\n")
            f.write(f"包含表情的评论比例: {self.df['has_emoji'].mean():.2%}\n")
            f.write(f"平均点赞数: {self.df['like_count'].mean():.1f}\n")
            f.write(f"平均回复数: {self.df['sub_comment_count'].mean():.1f}\n")
            f.write(f"平均创建到修改时间差: {self.df['time_diff_days'].mean():.2f}天\n\n")

            # 2. 地域分布分析
            f.write("2. 地域分布分析\n")
            f.write("-" * 40 + "\n")
            province_dist = self.df['province'].value_counts()
            for i, (province, count) in enumerate(province_dist.head(15).items(), 1):
                percentage = (count / len(self.df)) * 100
                f.write(f"{i:2d}. {province:<8}: {count:>4}条评论 ({percentage:5.2f}%)\n")
            f.write("\n")

            # 3. 时间分布分析
            f.write("3. 时间分布分析\n")
            f.write("-" * 40 + "\n")
            # 按小时分布
            hour_dist = self.df['hour'].value_counts().sort_index()
            f.write("按小时分布:\n")
            for hour, count in hour_dist.items():
                percentage = (count / len(self.df)) * 100
                f.write(f"  {hour:2d}时: {count:>4}条评论 ({percentage:5.2f}%)\n")

            # 按工作日分布
            f.write("\n按工作日分布:\n")
            weekday_dist = self.df['weekday'].value_counts().sort_index()
            days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
            for i, count in weekday_dist.items():
                percentage = (count / len(self.df)) * 100
                f.write(f"  {days[i]}: {count:>4}条评论 ({percentage:5.2f}%)\n")
            f.write("\n")

            # 4. 内容分析
            f.write("4. 内容分析\n")
            f.write("-" * 40 + "\n")
            # 评论长度分布
            f.write(f"最短评论长度: {self.df['content_length'].min()}字符\n")
            f.write(f"最长评论长度: {self.df['content_length'].max()}字符\n")
            f.write(f"评论长度中位数: {self.df['content_length'].median():.1f}字符\n")

            # 表情使用情况
            emoji_count = self.df['has_emoji'].sum()
            f.write(f"使用表情的评论数: {emoji_count} ({emoji_count / len(self.df) * 100:.2f}%)\n")
            f.write(
                f"未使用表情的评论数: {len(self.df) - emoji_count} ({(len(self.df) - emoji_count) / len(self.df) * 100:.2f}%)\n\n")

            # 5. 互动数据分析
            f.write("5. 互动数据分析\n")
            f.write("-" * 40 + "\n")
            f.write(f"总点赞数: {self.df['like_count'].sum()}\n")
            f.write(f"总回复数: {self.df['sub_comment_count'].sum()}\n")
            f.write(f"最高点赞数: {self.df['like_count'].max()}\n")
            f.write(f"最高回复数: {self.df['sub_comment_count'].max()}\n")

            # 高互动评论
            top_liked = self.df.nlargest(5, 'like_count')
            f.write("\n点赞数TOP5评论:\n")
            for i, (idx, row) in enumerate(top_liked.iterrows(), 1):
                f.write(f"  {i}. 点赞{row['like_count']}次: {row['content'][:50]}...\n")

            top_replied = self.df.nlargest(5, 'sub_comment_count')
            f.write("\n回复数TOP5评论:\n")
            for i, (idx, row) in enumerate(top_replied.iterrows(), 1):
                f.write(f"  {i}. 回复{row['sub_comment_count']}次: {row['content'][:50]}...\n")
            f.write("\n")

            # 6. 时间差分析
            f.write("6. 创建到修改时间差分析\n")
            f.write("-" * 40 + "\n")
            time_diff_stats = self.df['time_diff_days'].describe()
            f.write(f"最短时间差: {time_diff_stats['min']:.4f}天\n")
            f.write(f"最长时间差: {time_diff_stats['max']:.4f}天\n")
            f.write(f"中位数时间差: {time_diff_stats['50%']:.4f}天\n")

            # 时间差分段统计
            time_diff_bins = pd.cut(self.df['time_diff_days'],
                                    bins=[0, 1 / 24, 1 / 4, 1, 7, 30, float('inf')],
                                    labels=['<1小时', '1-6小时', '6-24小时', '1-7天', '7-30天', '>30天'])
            time_diff_counts = time_diff_bins.value_counts()
            f.write("\n时间差分段统计:\n")
            for label, count in time_diff_counts.items():
                percentage = (count / len(self.df)) * 100
                f.write(f"  {label}: {count:>4}条评论 ({percentage:5.2f}%)\n")
            f.write("\n")

            # 7. 热门视频分析
            f.write("7. 热门视频分析\n")
            f.write("-" * 40 + "\n")
            video_comments = self.df['aweme_id'].value_counts().head(10)
            f.write("评论数TOP10视频:\n")
            for i, (video_id, count) in enumerate(video_comments.items(), 1):
                percentage = (count / len(self.df)) * 100
                f.write(f"  {i:2d}. 视频ID {video_id}: {count:>4}条评论 ({percentage:5.2f}%)\n")
            f.write("\n")

            # 8. 活跃用户分析
            f.write("8. 活跃用户分析\n")
            f.write("-" * 40 + "\n")
            user_activity = self.df['user_id'].value_counts().head(15)
            f.write("评论数TOP15用户:\n")
            for i, (user_id, count) in enumerate(user_activity.items(), 1):
                percentage = (count / len(self.df)) * 100
                f.write(f"  {i:2d}. 用户ID {user_id}: {count:>4}条评论 ({percentage:5.2f}%)\n")
            f.write("\n")

            # 9. 关键词分析
            f.write("9. 评论关键词分析\n")
            f.write("-" * 40 + "\n")
            texts = self.df['content'].dropna().tolist()
            keywords = extract_keywords(texts, 20)
            f.write("评论内容TOP20关键词:\n")
            for i, (word, count) in enumerate(keywords, 1):
                f.write(f"  {i:2d}. {word}: {count}次\n")
            f.write("\n")

            # 10. 数据质量检查
            f.write("10. 数据质量检查\n")
            f.write("-" * 40 + "\n")
            missing_content = self.df['content'].isna().sum()
            missing_location = self.df['ip_location'].isna().sum()
            f.write(f"内容为空评论数: {missing_content} ({missing_content / len(self.df) * 100:.2f}%)\n")
            f.write(f"位置为空评论数: {missing_location} ({missing_location / len(self.df) * 100:.2f}%)\n")

            # 报告尾部
            f.write("\n" + "=" * 80 + "\n")
            f.write("报告结束\n")
            f.write("=" * 80 + "\n")

        print(f"TXT数据报告已保存: {report_filepath}")
        return report_filepath

    def create_seaborn_visualizations(self):
        """创建Seaborn可视化图表"""
        print("\n正在生成Seaborn可视化...")

        # 设置风格和字体
        sns.set_theme(style="whitegrid")

        # 创建图形时明确设置字体
        plt.figure(figsize=(24, 18))

        # 1. 评论时间分布（按小时）- 基于创建时间
        plt.subplot(4, 4, 1)
        hour_dist = self.df['hour'].value_counts().sort_index()
        ax1 = sns.barplot(x=hour_dist.index, y=hour_dist.values, palette="viridis")
        plt.title('评论创建时间分布（按小时）', fontsize=12, fontweight='bold', fontname='SimHei')
        plt.xlabel('小时', fontname='SimHei')
        plt.ylabel('评论数量', fontname='SimHei')
        # 设置刻度标签字体
        for label in ax1.get_xticklabels():
            label.set_fontname('SimHei')
        for label in ax1.get_yticklabels():
            label.set_fontname('SimHei')

        # 2. 地域分布（TOP10）
        plt.subplot(4, 4, 2)
        location_dist = self.df['province'].value_counts().head(10)
        ax2 = sns.barplot(y=location_dist.index, x=location_dist.values, palette="rocket")
        plt.title('评论地域分布TOP10', fontsize=12, fontweight='bold', fontname='SimHei')
        plt.xlabel('评论数量', fontname='SimHei')
        # 设置刻度标签字体
        for label in ax2.get_xticklabels():
            label.set_fontname('SimHei')
        for label in ax2.get_yticklabels():
            label.set_fontname('SimHei')

        # 3. 评论长度分布
        plt.subplot(4, 4, 3)
        ax3 = sns.histplot(data=self.df, x='content_length', bins=30, kde=True, color='skyblue')
        plt.title('评论长度分布', fontsize=12, fontweight='bold', fontname='SimHei')
        plt.xlabel('评论长度（字符）', fontname='SimHei')
        plt.ylabel('频次', fontname='SimHei')
        # 设置刻度标签字体
        for label in ax3.get_xticklabels():
            label.set_fontname('SimHei')
        for label in ax3.get_yticklabels():
            label.set_fontname('SimHei')

        # 4. 点赞数分布（取前100条避免长尾）
        plt.subplot(4, 4, 4)
        like_data = self.df.nlargest(min(100, len(self.df)), 'like_count')
        ax4 = sns.scatterplot(data=like_data, x=range(len(like_data)), y='like_count',
                              size='sub_comment_count', sizes=(20, 200), alpha=0.6)
        plt.title('高点赞评论分布', fontsize=12, fontweight='bold', fontname='SimHei')
        plt.xlabel('评论序号', fontname='SimHei')
        plt.ylabel('点赞数', fontname='SimHei')
        # 设置刻度标签字体
        for label in ax4.get_xticklabels():
            label.set_fontname('SimHei')
        for label in ax4.get_yticklabels():
            label.set_fontname('SimHei')

        # 5. 回复数分布
        plt.subplot(4, 4, 5)
        reply_data = self.df[self.df['sub_comment_count'] > 0]
        if len(reply_data) > 0:
            ax5 = sns.boxplot(data=reply_data, y='sub_comment_count', color='lightgreen')
            plt.title('回复数分布（有回复的评论）', fontsize=12, fontweight='bold', fontname='SimHei')
            plt.ylabel('回复数量', fontname='SimHei')
            # 设置刻度标签字体
            for label in ax5.get_yticklabels():
                label.set_fontname('SimHei')

        # 6. 工作日分布 - 基于创建时间
        plt.subplot(4, 4, 6)
        weekday_dist = self.df['weekday'].value_counts().sort_index()
        days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        ax6 = sns.barplot(x=[days[i] for i in weekday_dist.index], y=weekday_dist.values, palette="Set2")
        plt.title('评论创建时间-工作日分布', fontsize=12, fontweight='bold', fontname='SimHei')
        plt.xlabel('星期', fontname='SimHei')
        plt.ylabel('评论数量', fontname='SimHei')
        plt.xticks(rotation=0)
        # 设置刻度标签字体
        for label in ax6.get_xticklabels():
            label.set_fontname('SimHei')
        for label in ax6.get_yticklabels():
            label.set_fontname('SimHei')

        # 7. 表情使用情况
        plt.subplot(4, 4, 7)
        emoji_data = self.df['has_emoji'].value_counts()
        plt.pie(emoji_data.values, labels=['无表情', '有表情'], autopct='%1.1f%%',
                colors=['lightcoral', 'lightskyblue'], textprops={'fontfamily': 'SimHei'})
        plt.title('表情使用情况', fontsize=12, fontweight='bold', fontname='SimHei')

        # 8. 评论长度与点赞关系
        plt.subplot(4, 4, 8)
        sample_data = self.df.sample(min(500, len(self.df)))  # 抽样避免过度拥挤
        ax8 = sns.regplot(data=sample_data, x='content_length', y='like_count',
                          scatter_kws={'alpha': 0.5}, line_kws={'color': 'red'})
        plt.title('评论长度与点赞数关系', fontsize=12, fontweight='bold', fontname='SimHei')
        plt.xlabel('评论长度', fontname='SimHei')
        plt.ylabel('点赞数', fontname='SimHei')
        # 设置刻度标签字体
        for label in ax8.get_xticklabels():
            label.set_fontname('SimHei')
        for label in ax8.get_yticklabels():
            label.set_fontname('SimHei')

        # 9. 热门视频评论数TOP10
        plt.subplot(4, 4, 9)
        video_comments = self.df['aweme_id'].value_counts().head(10)
        ax9 = sns.barplot(y=[f"视频{i + 1}" for i in range(len(video_comments))],
                          x=video_comments.values, palette="coolwarm")
        plt.title('热门视频评论数TOP10', fontsize=12, fontweight='bold', fontname='SimHei')
        plt.xlabel('评论数量', fontname='SimHei')
        # 设置刻度标签字体
        for label in ax9.get_xticklabels():
            label.set_fontname('SimHei')
        for label in ax9.get_yticklabels():
            label.set_fontname('SimHei')

        # 10. 创建到修改时间差分布
        plt.subplot(4, 4, 10)
        time_diff_data = self.df[self.df['time_diff_days'] >= 0]  # 过滤负值
        ax10 = sns.histplot(data=time_diff_data, x='time_diff_days', bins=30, kde=True, color='orange')
        plt.title('创建到修改时间差分布', fontsize=12, fontweight='bold', fontname='SimHei')
        plt.xlabel('时间差（天）', fontname='SimHei')
        plt.ylabel('频次', fontname='SimHei')
        # 设置刻度标签字体
        for label in ax10.get_xticklabels():
            label.set_fontname('SimHei')
        for label in ax10.get_yticklabels():
            label.set_fontname('SimHei')

        # 11. 时间差与点赞数关系
        plt.subplot(4, 4, 11)
        sample_time_data = self.df[self.df['time_diff_days'] >= 0].sample(min(500, len(self.df)))
        ax11 = sns.scatterplot(data=sample_time_data, x='time_diff_days', y='like_count', alpha=0.6)
        plt.title('时间差与点赞数关系', fontsize=12, fontweight='bold', fontname='SimHei')
        plt.xlabel('时间差（天）', fontname='SimHei')
        plt.ylabel('点赞数', fontname='SimHei')
        # 设置刻度标签字体
        for label in ax11.get_xticklabels():
            label.set_fontname('SimHei')
        for label in ax11.get_yticklabels():
            label.set_fontname('SimHei')

        # 12. 每日评论数量趋势 - 基于创建时间
        plt.subplot(4, 4, 12)
        daily_counts = self.df.groupby('date').size().reset_index(name='count')
        ax12 = sns.lineplot(data=daily_counts, x='date', y='count', marker='o')
        plt.title('每日评论数量趋势', fontsize=12, fontweight='bold', fontname='SimHei')
        plt.xlabel('日期', fontname='SimHei')
        plt.ylabel('评论数量', fontname='SimHei')
        plt.xticks(rotation=0)
        # 设置刻度标签字体
        for label in ax12.get_xticklabels():
            label.set_fontname('SimHei')
        for label in ax12.get_yticklabels():
            label.set_fontname('SimHei')

        # 13. 用户评论频率分布
        plt.subplot(4, 4, 13)
        user_comment_counts = self.df['user_id'].value_counts()
        user_freq_dist = user_comment_counts.value_counts().sort_index().head(20)
        ax13 = sns.barplot(x=user_freq_dist.index, y=user_freq_dist.values, palette="plasma")
        plt.title('用户评论频率分布', fontsize=12, fontweight='bold', fontname='SimHei')
        plt.xlabel('评论次数', fontname='SimHei')
        plt.ylabel('用户数量', fontname='SimHei')
        # 设置刻度标签字体
        for label in ax13.get_xticklabels():
            label.set_fontname('SimHei')
        for label in ax13.get_yticklabels():
            label.set_fontname('SimHei')

        # 14. 评论长度与时间差关系
        plt.subplot(4, 4, 14)
        sample_data_14 = self.df[self.df['time_diff_days'] >= 0].sample(min(500, len(self.df)))
        ax14 = sns.scatterplot(data=sample_data_14, x='content_length', y='time_diff_days', alpha=0.6)
        plt.title('评论长度与时间差关系', fontsize=12, fontweight='bold', fontname='SimHei')
        plt.xlabel('评论长度', fontname='SimHei')
        plt.ylabel('时间差（天）', fontname='SimHei')
        # 设置刻度标签字体
        for label in ax14.get_xticklabels():
            label.set_fontname('SimHei')
        for label in ax14.get_yticklabels():
            label.set_fontname('SimHei')

        # 15. 时间差分段统计
        plt.subplot(4, 4, 15)
        # 修改分段区间为天
        time_diff_bins = pd.cut(self.df['time_diff_days'],
                                bins=[0, 1 / 24, 1 / 4, 1, 7, 30, float('inf')],
                                # <1小时, 1-6小时, 6-24小时, 1-7天, 7-30天, >30天
                                labels=['<1小时', '1-6小时', '6-24小时', '1-7天', '7-30天', '>30天'])
        time_diff_counts = time_diff_bins.value_counts()
        ax15 = sns.barplot(x=time_diff_counts.index, y=time_diff_counts.values, palette="cool")
        plt.title('时间差分段统计', fontsize=12, fontweight='bold', fontname='SimHei')
        plt.xlabel('时间差范围', fontname='SimHei')
        plt.ylabel('评论数量', fontname='SimHei')
        plt.xticks(rotation=0)
        # 设置刻度标签字体
        for label in ax15.get_xticklabels():
            label.set_fontname('SimHei')
        for label in ax15.get_yticklabels():
            label.set_fontname('SimHei')

        # 16. 活跃时间段分析
        plt.subplot(4, 4, 16)
        hour_avg_likes = self.df.groupby('hour')['like_count'].mean().reset_index()
        ax16 = sns.barplot(data=hour_avg_likes, x='hour', y='like_count', palette="viridis")
        plt.title('各时间段平均点赞数', fontsize=12, fontweight='bold', fontname='SimHei')
        plt.xlabel('小时', fontname='SimHei')
        plt.ylabel('平均点赞数', fontname='SimHei')
        # 设置刻度标签字体
        for label in ax16.get_xticklabels():
            label.set_fontname('SimHei')
        for label in ax16.get_yticklabels():
            label.set_fontname('SimHei')

        plt.tight_layout()
        plt.suptitle('抖音评论数据综合分析', fontsize=16, fontweight='bold', y=1.02, fontname='SimHei')

        # 保存图片到桌面comments文件夹
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"seaborn_comments_analysis_{timestamp}.png"
        filepath = os.path.join(self.output_folder, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        print(f"Seaborn可视化已保存: {filepath}")

    def create_pyecharts_visualizations(self):
        """创建Pyecharts交互式可视化"""
        print("\n正在生成Pyecharts可视化...")

        # 创建页面
        page = Page(layout=Page.SimplePageLayout)

        # 1. 地域分布地图
        # 使用省份数据而不是原始IP位置
        province_data = self.df['province'].value_counts()
        # 移除"未知"省份
        province_data = province_data[province_data.index != '未知']

        # 将省份名称转换为Pyecharts地图所需的格式
        province_map_data = []
        for province, count in province_data.items():
            # 确保省份名称与地图匹配
            if province == '黑龙江':
                province_map_data.append(('黑龙江', int(count)))
            elif province == '内蒙古':
                province_map_data.append(('内蒙古', int(count)))
            else:
                # 添加省、市、自治区等后缀以匹配地图标准名称
                if province in ['北京', '天津', '上海', '重庆']:
                    province_map_data.append((province + '市', int(count)))
                elif province in ['香港', '澳门']:
                    province_map_data.append((province + '特别行政区', int(count)))
                elif province in ['新疆', '西藏', '广西', '宁夏', '内蒙古']:
                    # 内蒙古已经单独处理
                    if province != '内蒙古':
                        province_map_data.append((province + '自治区', int(count)))
                else:
                    province_map_data.append((province + '省', int(count)))

        # 检查是否有数据
        if province_map_data:
            max_count = max([count for _, count in province_map_data])
        else:
            max_count = 1  # 防止除以零

        # 创建颜色分段
        pieces = []
        if max_count > 0:
            # 根据最大值创建分段
            step = max(1, max_count // 5)  # 分成5段
            for i in range(5):
                min_val = i * step
                max_val = (i + 1) * step if i < 4 else max_count
                color_index = i
                color_list = ['#FFEFD5', '#FFD700', '#FFA500', '#FF6347', '#FF0000']
                pieces.append({
                    "min": min_val,
                    "max": max_val,
                    "label": f"{min_val}-{max_val}",
                    "color": color_list[color_index]
                })

        map_chart = (
            Map(init_opts=opts.InitOpts(
                theme=ThemeType.ROMA,
                width="1200px",
                height="600px"
            ))
            .add(
                series_name="评论数量",
                data_pair=province_map_data,
                maptype="china",
                is_map_symbol_show=False,
                label_opts=opts.LabelOpts(is_show=True, font_size=8, formatter="{b}\n{c}"),
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title="评论地域分布热力图",
                    subtitle="基于省份级别的分析"
                ),
                visualmap_opts=opts.VisualMapOpts(
                    max_=max_count,
                    min_=0,
                    is_piecewise=True,
                    pieces=pieces,
                    pos_top="middle",
                    pos_left="left",
                    orient="vertical"
                ),
                legend_opts=opts.LegendOpts(is_show=False),
            )
        )
        page.add(map_chart)

        # 2. 时间趋势折线图 - 基于创建时间
        time_data = self.df.groupby('date').size().reset_index(name='count')
        time_data = time_data.sort_values('date')

        line_chart = (
            Line(init_opts=opts.InitOpts(
                theme=ThemeType.MACARONS,
                width="1200px",
                height="500px"
            ))
            .add_xaxis(time_data['date'].astype(str).tolist())
            .add_yaxis(
                series_name="评论数量",
                y_axis=time_data['count'].tolist(),
                is_smooth=True,
                symbol="circle",
                symbol_size=6,
                linestyle_opts=opts.LineStyleOpts(width=3),
                label_opts=opts.LabelOpts(is_show=False),
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title="评论创建时间趋势"),
                tooltip_opts=opts.TooltipOpts(trigger="axis"),
                xaxis_opts=opts.AxisOpts(
                    type_="category",
                    name="日期",
                    axislabel_opts=opts.LabelOpts(rotate=0)
                ),
                yaxis_opts=opts.AxisOpts(name="评论数量"),
                datazoom_opts=[opts.DataZoomOpts()],
            )
        )
        page.add(line_chart)

        # 3. 词云图
        texts = self.df['content'].dropna().tolist()
        keywords = extract_keywords(texts, 100)

        wordcloud = (
            WordCloud(init_opts=opts.InitOpts(
                theme=ThemeType.WESTEROS,
                width="1000px",
                height="600px"
            ))
            .add(
                series_name="评论关键词",
                data_pair=keywords,
                word_size_range=[20, 100],
                rotate_step=0,
                shape=SymbolType.DIAMOND
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title="评论内容词云分析",
                    title_textstyle_opts=opts.TextStyleOpts(font_size=20)
                ),
                tooltip_opts=opts.TooltipOpts(is_show=True),
            )
        )
        page.add(wordcloud)

        # 4. 点赞分布圆盘图
        like_ranges = pd.cut(self.df['like_count'],
                             bins=[-1, 0, 1, 5, 10, 50, 100, float('inf')],
                             labels=['0', '1', '2-5', '6-10', '11-50', '51-100', '100+'])
        like_dist = like_ranges.value_counts()

        pie_data = [(str(label), int(count)) for label, count in like_dist.items()]

        pie_chart = (
            Pie(init_opts=opts.InitOpts(
                theme=ThemeType.CHALK,
                width="1000px",
                height="600px"
            ))
            .add(
                series_name="点赞数分布",
                data_pair=pie_data,
                radius=["30%", "75%"],
                center=["50%", "50%"],
                rosetype="radius"
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title="评论点赞数分布圆盘图",
                    pos_left="center",
                    pos_top="20px"
                ),
                legend_opts=opts.LegendOpts(
                    orient="vertical",
                    pos_left="left"
                )
            )
            .set_series_opts(
                label_opts=opts.LabelOpts(formatter="{b}: {c} ({d}%)")
            )
        )
        page.add(pie_chart)

        # 5. 时间差分布图 - 更新为天单位
        time_diff_data = self.df[self.df['time_diff_days'] >= 0]['time_diff_days']
        # 更新分段区间为天
        time_diff_ranges = pd.cut(time_diff_data,
                                  bins=[0, 1 / 24, 1 / 4, 1, 7, 30, float('inf')],
                                  labels=['<1小时', '1-6小时', '6-24小时', '1-7天', '7-30天', '>30天'])
        time_diff_dist = time_diff_ranges.value_counts()

        time_diff_pie_data = [(str(label), int(count)) for label, count in time_diff_dist.items()]

        time_diff_pie = (
            Pie(init_opts=opts.InitOpts(
                theme=ThemeType.SHINE,
                width="1000px",
                height="600px"
            ))
            .add(
                series_name="创建到修改时间差分布",
                data_pair=time_diff_pie_data,
                radius=["30%", "75%"],
                center=["50%", "50%"],
                rosetype="area"
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title="评论创建到修改时间差分布",
                    pos_left="center",
                    pos_top="20px"
                ),
                legend_opts=opts.LegendOpts(
                    orient="vertical",
                    pos_left="left"
                )
            )
            .set_series_opts(
                label_opts=opts.LabelOpts(formatter="{b}: {c} ({d}%)")
            )
        )
        page.add(time_diff_pie)

        # 6. 互动数据柱状图
        top_comments = self.df.nlargest(15, 'like_count')

        bar_chart = (
            Bar(init_opts=opts.InitOpts(
                theme=ThemeType.ESSOS,
                width="1200px",
                height="600px"
            ))
            .add_xaxis([f"评论{i + 1}" for i in range(len(top_comments))])
            .add_yaxis(
                "点赞数",
                top_comments['like_count'].tolist(),
                yaxis_index=0,
                color=JsCode("""
                function(params) {
                    var colorList = ['#c23531','#2f4554','#61a0a8','#d48265','#91c7ae','#749f83','#ca8622','#bda29a'];
                    return colorList[params.dataIndex % colorList.length];
                }
                """)
            )
            .add_yaxis(
                "回复数",
                top_comments['sub_comment_count'].tolist(),
                yaxis_index=1,
            )
            .extend_axis(
                yaxis=opts.AxisOpts(
                    name="回复数",
                    type_="value",
                    min_=0,
                    position="right",
                    axisline_opts=opts.AxisLineOpts(
                        linestyle_opts=opts.LineStyleOpts(color="#d48265")
                    ),
                    axislabel_opts=opts.LabelOpts(formatter="{value}"),
                )
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title="高互动评论分析"),
                tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross"),
                xaxis_opts=opts.AxisOpts(
                    type_="category",
                    axislabel_opts=opts.LabelOpts(rotate=0)
                ),
                yaxis_opts=opts.AxisOpts(
                    name="点赞数",
                    type_="value",
                    min_=0,
                    position="left",
                    axisline_opts=opts.AxisLineOpts(
                        linestyle_opts=opts.LineStyleOpts(color="#c23531")
                    ),
                ),
                datazoom_opts=[opts.DataZoomOpts()],
            )
        )
        page.add(bar_chart)

        # 7. 用户活跃度分析
        user_activity = self.df['user_id'].value_counts().head(20)

        user_bar = (
            Bar(init_opts=opts.InitOpts(
                theme=ThemeType.PURPLE_PASSION,
                width="1200px",
                height="600px"
            ))
            .add_xaxis([f"用户{i + 1}" for i in range(len(user_activity))])
            .add_yaxis(
                "评论数量",
                user_activity.values.tolist(),
                label_opts=opts.LabelOpts(is_show=True)
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title="活跃用户TOP20"),
                xaxis_opts=opts.AxisOpts(
                    axislabel_opts=opts.LabelOpts(rotate=0)
                ),
                yaxis_opts=opts.AxisOpts(name="评论数量"),
            )
        )
        page.add(user_bar)

        # 8. 时间段互动分析
        hour_interaction = self.df.groupby('hour').agg({
            'like_count': 'mean',
            'sub_comment_count': 'mean',
            'user_id': 'count'
        }).reset_index()

        hour_line = (
            Line(init_opts=opts.InitOpts(
                theme=ThemeType.ROMA,
                width="1200px",
                height="600px"
            ))
            .add_xaxis(hour_interaction['hour'].tolist())
            .add_yaxis(
                "平均点赞数",
                hour_interaction['like_count'].round(2).tolist(),
                yaxis_index=0,
                linestyle_opts=opts.LineStyleOpts(width=3),
                label_opts=opts.LabelOpts(is_show=False),
            )
            .add_yaxis(
                "平均回复数",
                hour_interaction['sub_comment_count'].round(2).tolist(),
                yaxis_index=1,
                linestyle_opts=opts.LineStyleOpts(width=3),
                label_opts=opts.LabelOpts(is_show=False),
            )
            .extend_axis(
                yaxis=opts.AxisOpts(
                    name="平均回复数",
                    type_="value",
                    min_=0,
                    position="right",
                    axisline_opts=opts.AxisLineOpts(
                        linestyle_opts=opts.LineStyleOpts(color="#d48265")
                    ),
                )
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title="各时间段互动情况分析"),
                tooltip_opts=opts.TooltipOpts(trigger="axis"),
                xaxis_opts=opts.AxisOpts(
                    type_="category",
                    name="小时"
                ),
                yaxis_opts=opts.AxisOpts(
                    name="平均点赞数",
                    type_="value",
                    min_=0,
                    position="left",
                ),
            )
        )
        page.add(hour_line)

        # 9. 省份分布柱状图
        province_bar = (
            Bar(init_opts=opts.InitOpts(
                theme=ThemeType.WALDEN,
                width="1200px",
                height="600px"
            ))
            .add_xaxis(province_data.index.tolist())
            .add_yaxis(
                "评论数量",
                province_data.values.tolist(),
                label_opts=opts.LabelOpts(is_show=True),
                itemstyle_opts=opts.ItemStyleOpts(
                    color=JsCode("""
                    function(params) {
                        var colorList = [
                            '#c23531','#2f4554','#61a0a8','#d48265','#91c7ae',
                            '#749f83','#ca8622','#bda29a','#6e7074','#546570'
                        ];
                        return colorList[params.dataIndex % colorList.length];
                    }
                    """)
                )
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title="评论省份分布"),
                xaxis_opts=opts.AxisOpts(
                    axislabel_opts=opts.LabelOpts(rotate=0)
                ),
                yaxis_opts=opts.AxisOpts(name="评论数量"),
            )
            .set_series_opts(
                label_opts=opts.LabelOpts(
                    position="top",
                    formatter="{c}"
                )
            )
        )
        page.add(province_bar)

        # 保存HTML文件到桌面comments文件夹
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"pyecharts_comments_analysis_{timestamp}.html"
        output_filepath = os.path.join(self.output_folder, output_filename)
        page.render(output_filepath)
        print(f"Pyecharts可视化已保存: {output_filepath}")

        return output_filepath

    def run_analysis(self):
        """运行完整分析流程"""
        print("开始评论数据分析...")
        print("=" * 50)

        self.analyze_basic_stats()
        self.generate_txt_report()  # 生成TXT报告
        self.create_seaborn_visualizations()
        self.create_pyecharts_visualizations()

        print("\n" + "=" * 50)
        print(f"所有文件已保存到: {self.output_folder}")
        print("数据分析完成！")


"""
主程序入口
"""
if __name__ == "__main__":
    # 指定目录路径
    # D:\\MediaCrawler-main\\data
    directory = "D:\\MediaCrawler-main\\data"

    # 使用 glob 查找以 "creator_comments" 开头的 CSV 文件
    csv_files = glob.glob(os.path.join(directory, "creator_comments*.csv"))

    if not csv_files:
        print(f"在目录 {directory} 中未找到以 'creator_comments' 开头的 CSV 文件")
        exit(1)

    # 这里选择按修改时间排序，取最新的文件
    csv_files.sort(key=os.path.getmtime, reverse=True)
    csv_file1 = csv_files[0]

    print(f"找到 CSV 文件: {csv_file1}")

    # 初始化分析器
    analyzer = CommentDataAnalyzer(csv_file1)

    # 运行分析
    analyzer.run_analysis()
