import pandas as pd
from sqlalchemy import create_engine

class DataCleaner:
    def __init__(self, db_url):
        """
        初始化数据库连接
        参数:
            db_url: 数据库连接字符串
                   - MySQL: "mysql+pymysql://user:password@host:port/database"
                   - PostgreSQL: "postgresql://user:password@host:port/database"
                   - SQLite: "sqlite:///your.db"
        """
        self.engine = create_engine(db_url)

    def read_data(self, table_name, columns):
        """
        从数据库读取指定字段
        """
        query = f"SELECT {', '.join(columns)} FROM {table_name}"
        df = pd.read_sql(query, self.engine)
        return df

    def clean(self, df, columns_to_clean):
        """
        数据清洗逻辑：
        1. 去空值
        2. 去 0 值
        3. 箱型图法去异常值
        """
        cleaned_df = df.copy()

        for col in columns_to_clean:
            if col not in cleaned_df.columns:
                print(f"⚠️ 警告：字段 {col} 不存在，跳过")
                continue

            # 去空值和 0 值
            cleaned_df = cleaned_df[cleaned_df[col].notnull()]
            cleaned_df = cleaned_df[cleaned_df[col] != 0]

            # 箱型图方法去异常值
            Q1 = cleaned_df[col].quantile(0.25)
            Q3 = cleaned_df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            before_len = len(cleaned_df)
            cleaned_df = cleaned_df[(cleaned_df[col] >= lower_bound) & (cleaned_df[col] <= upper_bound)]
            after_len = len(cleaned_df)

            print(f"字段 {col} 清洗完成：移除了 {before_len - after_len} 条异常值")

        return cleaned_df

    def save_to_new_table(self, df, new_table_name, if_exists="replace"):
        """
        将清洗后的数据写入新的表
        参数:
            df: 清洗后的 DataFrame
            new_table_name: 新表名
            if_exists: 'replace' 覆盖, 'append' 追加
        """
        df.to_sql(new_table_name, self.engine, index=False, if_exists=if_exists)
        print(f"✅ 清洗后的数据已保存到新表: {new_table_name}")


# ================= 使用示例 =================
if __name__ == "__main__":
    # 数据库连接 (以 MySQL 为例)
    db_url = "mysql+pymysql://root:123456@localhost:3306/testdb"
    cleaner = DataCleaner(db_url)

    # 原始表和清洗后的表
    source_table = "gateway_data"
    new_table = "gateway_data_cleaned"

    # 需要清洗的字段
    columns_to_clean = ["temperature", "humidity", "pressure"]

    # 读取数据
    df = cleaner.read_data(source_table, columns_to_clean)
    print("原始数据：")
    print(df.head())

    # 清洗数据
    cleaned_df = cleaner.clean(df, columns_to_clean)

    # 保存到新表
    cleaner.save_to_new_table(cleaned_df, new_table)
