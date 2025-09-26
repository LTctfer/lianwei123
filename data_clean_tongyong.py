import pandas as pd
from sqlalchemy import create_engine

class DataCleaner:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)

    def read_data(self, table_name, columns, time_col):
        """
        从数据库读取数据，并确保时间字段转换为 datetime 类型
        """
        query = f"SELECT {', '.join(columns)} FROM {table_name}"
        df = pd.read_sql(query, self.engine)
        df[time_col] = pd.to_datetime(df[time_col])  # 确保时间列为 datetime 类型
        return df

    def clean_and_calculate(self, df, columns_to_clean, time_col="timestamp"):
        """
        在每个 1 分钟窗口内进行清洗并计算均值：
        1. 去空值
        2. 去 0 值
        3. 用箱型图去除极大值和极小值
        4. 计算均值
        """
        # 按分钟对时间戳取整
        df["minute"] = df[time_col].dt.floor("T")

        result_list = []

        for minute, group in df.groupby("minute"):
            group_cleaned = group.copy()

            # 清洗每一列
            for col in columns_to_clean:
                if col not in group_cleaned.columns:
                    continue

                # 去空值 & 0 值
                group_cleaned = group_cleaned[group_cleaned[col].notnull()]
                group_cleaned = group_cleaned[group_cleaned[col] != 0]

                # 箱型图方法去除极值
                if not group_cleaned.empty:
                    Q1 = group_cleaned[col].quantile(0.25)
                    Q3 = group_cleaned[col].quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    group_cleaned = group_cleaned[
                        (group_cleaned[col] >= lower_bound) &
                        (group_cleaned[col] <= upper_bound)
                    ]

            # 计算均值
            if not group_cleaned.empty:
                means = group_cleaned[columns_to_clean].mean()
                means[time_col] = minute  # 添加时间列
                result_list.append(means)

        # 将均值合并为 DataFrame
        result_df = pd.DataFrame(result_list)

        return result_df

    def save_to_backend(self, df, backend_function):
        """
        将计算后的均值写入后端
        参数：
            df: 清洗和计算后的 DataFrame
            backend_function: 后端接口函数
        """
        # 将均值结果传给后端
        for _, row in df.iterrows():
            backend_function(row)  # 调用后端接口
        print(f"✅ 已将数据写入后端：{len(df)} 条记录")


# ================= 使用示例 =================
if __name__ == "__main__":
    # 数据库连接
    db_url = "mysql+pymysql://root:123456@localhost:3306/testdb"
    cleaner = DataCleaner(db_url)

    # 表和字段
    source_table = "gateway_data"
    columns_to_clean = ["temperature", "humidity", "pressure"]
    time_col = "timestamp"

    # 后端函数示例（模拟）
    def backend_function(data_row):
        print(f"将数据写入后端：{data_row.to_dict()}")

    # 读取数据
    df = cleaner.read_data(source_table, [time_col] + columns_to_clean, time_col)
    print("原始数据：")
    print(df.head())

    # 清洗数据并计算均值
    result_df = cleaner.clean_and_calculate(df, columns_to_clean, time_col)

    # 打印结果（均值）
    print("\n计算后的均值：")
    print(result_df)

    # 保存到后端
    cleaner.save_to_backend(result_df, backend_function)
