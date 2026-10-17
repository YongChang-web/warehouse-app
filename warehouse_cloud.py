import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(page_title="云端仓储管理系统", layout="wide")

# =========【这里可以自己改访问密码】=========
ACCESS_PASSWORD = "123654"
# ==========================================

# 读取密钥
supabase_url = st.secrets["supabase_url"]
supabase_anon_key = st.secrets["supabase_anon_key"]
supabase = create_client(supabase_url, supabase_anon_key)

# =========简易单密码验证=========
if "passed" not in st.session_state:
    st.session_state.passed = False

if not st.session_state.passed:
    st.title("🔐仓储系统访问入口")
    input_pw = st.text_input("请输入访问密码", type="password")
    if st.button("进入系统"):
        if input_pw == ACCESS_PASSWORD:
            st.session_state.passed = True
            st.rerun()
        else:
            st.error("❌密码不正确！")
    st.stop()

# =========主菜单========
st.sidebar.info("✅已通过密码验证")
menu = st.sidebar.selectbox("功能菜单",
    ["📦查看库存","➕新增商品","📥批量导入Excel","✏️修改商品","🗑️删除商品","💰销售出库","📊销售台账","📤导出报表"])
warn_line = st.sidebar.number_input("库存预警线", value=10, min_value=0)

# 1.查看库存
if menu == "📦查看库存":
    st.subheader("📦商品库存清单")
    res = supabase.table("goods").select("*").execute()
    df = pd.DataFrame(res.data)
    if len(df) ==0:
        st.info("暂无商品")
    else:
        def warn_style(row):
            if row["stock"] <= warn_line:
                return ['background-color:#ffcccc']*len(row)
            else:
                return ['']*len(row)
        st.dataframe(df.style.apply(warn_style,axis=1),use_container_width=True)

#2.新增商品
elif menu == "➕新增商品":
    st.subheader("➕新增商品入库")
    with st.form("add_form"):
        style = st.text_input("款式(style)")
        color = st.text_input("颜色(color)")
        price = st.number_input("单价(price)",0.0)
        stock = st.number_input("库存(stock)",0)
        sold = st.number_input("已售(sold)",0)
        pic = st.file_uploader("上传商品图片",type=["jpg","png","jpeg"])
        submit = st.form_submit_button("✅提交入库")
        if submit:
            img_url = ""
            if pic is not None:
                bucket_name="product-images"
                file_path = f"sys_{pic.name}"
                supabase.storage.from_(bucket_name).upload(file_path, pic.getvalue())
                img_url = f"{supabase_url}/storage/v1/object/public/{bucket_name}/{file_path}"
            supabase.table("goods").insert({
                "style":style,"color":color,"price":price,"stock":stock,"sold":sold,"imgpath":img_url
            }).execute()
            st.success("✅添加成功！")

#3.批量导入
elif menu == "📥批量导入Excel":
    st.info("⚠️Excel表头必须小写英文：style,color,price,stock,sold,imgpath")
    upfile = st.file_uploader("上传Excel",type=["xlsx"])
    if upfile is not None:
        df_upload = pd.read_excel(upfile)
        need_cols = {"style","color","price","stock","sold","imgpath"}
        if need_cols.issubset(df_upload.columns):
            data_list = df_upload.to_dict("records")
            supabase.table("goods").insert(data_list).execute()
            st.success("✅批量导入完成！")
        else:
            st.error("❌表头不对！")

#4.修改商品
elif menu == "✏️修改商品":
    st.subheader("✏️修改商品（填入ID）")
    edit_id = st.number_input("商品ID",min_value=1,step=1)
    res_one = supabase.table("goods").select("*").eq("id",edit_id).execute()
    if len(res_one.data)>0:
        d = res_one.data[0]
        with st.form("edit_f"):
            style = st.text_input("款式",value=d["style"])
            color = st.text_input("颜色",value=d["color"])
            price = st.number_input("单价",0.0,value=float(d["price"]))
            stock = st.number_input("库存",0,value=d["stock"])
            sold = st.number_input("已售",0,value=d["sold"])
            submit_e = st.form_submit_button("💾保存修改")
            if submit_e:
                supabase.table("goods").update({
                    "style":style,"color":color,"price":price,"stock":stock,"sold":sold
                }).eq("id",edit_id).execute()
                st.success("✅已更新！")
    else:
        st.warning("未找到该ID商品")

#5.删除
elif menu == "🗑️删除商品":
    st.subheader("🗑️删除商品（谨慎！）")
    del_id = st.number_input("要删除的商品ID",min_value=1,step=1)
    if st.button("⚠️确认删除"):
        supabase.table("goods").delete().eq("id",del_id).execute()
        st.success("✅已删除！")

#6.销售出库
elif menu == "💰销售出库":
    st.subheader("💰销售出库登记")
    sel_id = st.number_input("商品ID",min_value=1,step=1)
    r = supabase.table("goods").select("*").eq("id",sel_id).execute()
    if len(r.data)>0:
        item = r.data[0]
        st.write(f"款式：{item['style']}｜颜色：{item['color']}｜当前库存：{item['stock']}")
        sell_num = st.number_input("售出数量",min_value=1,max_value=item["stock"])
        sell_p = st.number_input("售卖单价",0.0,value=float(item["price"]))
        if st.button("✅确认售出"):
            new_stock = item["stock"] - sell_num
            new_sold = item["sold"] + sell_num
            supabase.table("goods").update({"stock":new_stock,"sold":new_sold}).eq("id",sel_id).execute()
            supabase.table("sales").insert({
                "goods_id":sel_id,
                "sell_num":sell_num,
                "sell_price":sell_p,
                "operator":"内部使用者"
            }).execute()
            st.success("✅出库成功，台账已自动记录！")
    else:
        st.info("请输入有效的商品ID")

#7.销售台账
elif menu == "📊销售台账":
    st.subheader("📊销售记录台账")
    s_res = supabase.table("sales").select("*").execute()
    s_df = pd.DataFrame(s_res.data)
    st.dataframe(s_df,use_container_width=True)

#8.导出报表
elif menu == "📤导出报表":
    st.subheader("📤导出库存报表")
    out = supabase.table("goods").select("*").execute()
    df_out = pd.DataFrame(out.data)
    csv = df_out.to_csv(index=False,encoding="utf-8-sig")
    st.download_button("📥下载库存CSV",csv,"inventory.csv","text/csv")
