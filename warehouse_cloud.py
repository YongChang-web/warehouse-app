import streamlit as st
import pandas as pd
from supabase import create_client, Client

# =========读取密钥=========
url: str = st.secrets["supabase_url"]
key: str = st.secrets["supabase_anon_key"]
supabase: Client = create_client(url, key)

# ---------- 语言配置 ----------
lang_dict = {
    "zh":{
        "title":"📦简易云端仓储管理系统",
        "menu_import":"📥导入Excel商品表",
        "menu_goods":"🏷️商品录入与查询",
        "menu_customer":"👤买家信息登记",
        "menu_report":"📊库存报表",
        "lang_switch":"🌐切换语言",
        "style":"款式",
        "color":"颜色",
        "price":"价格",
        "stock":"库存数量",
        "sold":"售出数量",
        "imgpath":"图片路径",
        "name":"客户姓名",
        "phone":"联系电话",
        "note":"备注",
        "save":"💾保存",
        "export":"📤导出报表",
        "warning_no_data":"暂无数据，请先导入或录入商品！"
    },
    "en":{
        "title":"📦 Simple Cloud Warehouse System",
        "menu_import":"📥 Import Excel Goods",
        "menu_goods":"🏷️ Goods Entry & Search",
        "menu_customer":"👤 Customer Record",
        "menu_report":"📊 Stock Report",
        "lang_switch":"🌐 Switch Language",
        "style":"Style",
        "color":"Color",
        "price":"Price",
        "stock":"Stock Qty",
        "sold":"Sold Qty",
        "imgpath":"Image Path",
        "name":"Customer Name",
        "phone":"Phone",
        "note":"Note",
        "save":"💾 Save",
        "export":"📤 Export Report",
        "warning_no_data":"No data! Please import or add goods first."
    }
}

# 初始化语言
if 'language' not in st.session_state:
    st.session_state.language = "zh"

lang_opt = st.radio(lang_dict[st.session_state.language]["lang_switch"],["中文","English"])
if lang_opt == "中文":
    st.session_state.language = "zh"
else:
    st.session_state.language = "en"
L = lang_dict[st.session_state.language]

st.title(L["title"])
menu = st.sidebar.selectbox("Menu",
    [L["menu_import"],L["menu_goods"],L["menu_customer"],L["menu_report"]])

# 1.导入Excel
if menu == L["menu_import"]:
    st.subheader(L["menu_import"])
    upfile = st.file_uploader("Upload Excel",type=["xlsx"])
    if upfile is not None:
        try:
            df = pd.read_excel(upfile)
            progress_bar = st.progress(0)
            for i,row in df.iterrows():
                data = {
                    "style":str(row.get("style","")),
                    "color":str(row.get("color","")),
                    "price":float(row.get("price",0)),
                    "stock":int(row.get("stock",0)),
                    "sold":int(row.get("sold",0)),
                    "imgpath":str(row.get("imgpath",""))
                }
                supabase.table("goods").insert(data).execute()
                progress_bar.progress((i+1)/len(df))
            st.success("✅全部导入云数据库成功！")
        except Exception as e:
            st.error(str(e))

#2.商品录入
if menu == L["menu_goods"]:
    st.subheader(L["menu_goods"])
    with st.form("goods_form"):
        s = st.text_input(L["style"])
        c = st.text_input(L["color"])
        p = st.number_input(L["price"],0.0)
        stk = st.number_input(L["stock"],0)
        sl = st.number_input(L["sold"],0)
        img = st.text_input(L["imgpath"])
        sub = st.form_submit_button(L["save"])
        if sub:
            insert_data = {"style":s,"color":c,"price":p,"stock":stk,"sold":sl,"imgpath":img}
            supabase.table("goods").insert(insert_data).execute()
            st.success("✅已保存到云端！")
    #读取展示
    res = supabase.table("goods").select("*").execute()
    df_goods = pd.DataFrame(res.data)
    st.dataframe(df_goods)

#3.买家登记
if menu == L["menu_customer"]:
    st.subheader(L["menu_customer"])
    with st.form("cust_form"):
        n = st.text_input(L["name"])
        ph = st.text_input(L["phone"])
        nt = st.text_input(L["note"])
        subc = st.form_submit_button(L["save"])
        if subc:
            cust_data = {"name":n,"phone":ph,"note":nt}
            supabase.table("customers").insert(cust_data).execute()
            st.success("✅买家信息存入云端！")
    res_c = supabase.table("customers").select("*").execute()
    df_cust = pd.DataFrame(res_c.data)
    st.dataframe(df_cust)

#4.库存报表
if menu == L["menu_report"]:
    st.subheader(L["menu_report"])
    res = supabase.table("goods").select("*").execute()
    df = pd.DataFrame(res.data)
    if len(df)>0:
        df["Available"] = df["stock"] - df["sold"]
        st.dataframe(df)
        #下载
        from io import BytesIO
        output = BytesIO()
        with pd.ExcelWriter(output,engine="openpyxl") as writer:
            df.to_excel(writer,index=False,sheet_name="Stock")
        output.seek(0)
        st.download_button(L["export"],data=output,file_name="StockReport.xlsx")
    else:
        st.warning(L["warning_no_data"])

st.markdown("---")
st.caption("🌐云端协同仓储系统｜数据存储于Supabase")