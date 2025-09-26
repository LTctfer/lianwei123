import pandas as pd

def clean_data(df, columns_to_clean):
    """
    通用数据清洗函数：
    1. 去除空值
    2. 去除 0 值
    3. 使用箱型图(IQR)去除异常值

    参数:
        df (pd.DataFrame): 输入的原始数据
        columns_to_clean (list): 需要清洗的字段名列表

    返回:
        pd.DataFrame: 清洗后的数据
    """
    cleaned_df = df.copy()

    for col in columns_to_clean:
        if col not in cleaned_df.columns:
            print(f"⚠️ 警告：字段 {col} 不存在，跳过")
            continue

        # 去除空值和 0 值
        cleaned_df = cleaned_df[cleaned_df[col].notnull()]
        cleaned_df = cleaned_df[cleaned_df[col] != 0]

        # 使用箱型图方法去除异常值
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


# ================= 使用示例 =================
if __name__ == "__main__":
    # 构造示例数据
    data = {
        "温度": [25, 26, 0, None, 1000, 27, 28],
        "湿度": [50, 55, 60, 0, None, 70, 800],
        "压力": [101, 102, 103, 104, 0, None, 10000]
    }
    df = pd.DataFrame(data)
    print("原始数据：")
    print(df)

    # 只需要修改这部分即可指定清洗的字段
    columns_to_clean = ["温度", "湿度", "压力"]

    cleaned = clean_data(df, columns_to_clean)
    print("\n清洗后的数据：")
    print(cleaned)
