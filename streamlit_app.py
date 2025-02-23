import streamlit as st
import sys
import traceback

try:
    import numpy as np
    import pandas as pd
    import plotly.express as px
    import pickle
    from pysurvival.utils import load_model
except Exception as e:
    st.error(f"Error loading dependencies: {str(e)}")
    st.code(traceback.format_exc())
    sys.exit(1)

st.set_page_config(layout="wide")

@st.cache_data(show_spinner=False)
def load_setting():
    # 定义与训练时完全一致的映射关系
    level_mapping = {
        'Diagnosis Year': {"<2020": 0, "≥2020": 1},  # covid in R code
        'Molecular Pathology Types': {  # type in R code
            "Oligodendroglioma, IDH-mutant and 1p/19q-codeleted": 0,  # "O"
            "Glioblastoma, IDH-wildtype": 1,  # "GBM"
            "Astrocytoma, IDH-mutant": 2,  # "A"
        },
        'Gender': {"Female": 0, "Male": 1},  # matches sex F/M mapping
        'Race': {
            "White": 0,  # "W"
            "Black": 1,  # "B"
            "Asian or Pacific Islander": 2,  # "API"
            "American Indian/Alaska Native": 3,  # "AI"
            "Unknown": 4,  # "missing"
        },
        'Marrital status': {
            "Married": 0,  # "married"
            "Single": 1,  # "single"
            "Unknown": 2,  # "missing"
        },
        'Location of the tumor': {  # site in R code
            "Frontal": 0,
            "Parietal": 1,
            "Occipital": 2,
            "Temporal": 3,
            "Ventricle": 4,
            "Cerebellum": 5,
            "Cerebrum": 6,
            "Overlap": 7,
            "Brainstem": 8,
            "missing": 9,
        },
        'Extent of disease': {  # eod in R code
            "Local": 0,  # "local"
            "Extensive": 1,  # "extension"
        },
        'Extent of resection': {  # resection in R code
            "Gross Total resection": 0,  # "GTR"
            "Subtotal resection/Partial resection": 1,  # "STR/PR"
            "Partial lobectomy": 2,  # "partiallobectomy"
            "Lobectomy": 3,  # "lobectomy"
            "Biopsy": 4,  # "auto"
            "Unknown": 5,  # "missing"
        },
        'Radiation': {
            "Yes": 0,
            "None/Unknown": 1,  # "None_or_Unknown"
        },
        'Chemotherapy': {
            "Yes": 0,
            "None/Unknown": 1,  # "No_or_Unknown"
        },
    }
    
    # 更新 settings 字典以匹配映射
    settings = {
        'Diagnosis Year': {'values': ["<2020", "≥2020"], 'type': 'selectbox', 'init_value': 0, 'add_after': ''}, 
        'Age': {'values': [0, 100], 'type': 'slider', 'init_value': 65, 'add_after': ', year'},
        'Molecular Pathology Types': {
            'values': [
                "Oligodendroglioma, IDH-mutant and 1p/19q-codeleted",
                "Glioblastoma, IDH-wildtype",
                "Astrocytoma, IDH-mutant"
            ],
            'type': 'selectbox',
            'init_value': 0,
            'add_after': ''
        },
        'Gender': {'values': ["Female", "Male"], 'type': 'selectbox', 'init_value': 0, 'add_after': ''},
        'Marrital status': {'values': ["Married", "Single", "Unknown"], 'type': 'selectbox', 'init_value': 0, 'add_after': ''},
        'Race': {
            'values': ["White", "Black", "Asian or Pacific Islander", "American Indian/Alaska Native", "Unknown"],
            'type': 'selectbox',
            'init_value': 0,
            'add_after': ''
        },
        'Location of the tumor': {
            'values': ["Frontal", "Parietal", "Occipital", "Temporal", "Ventricle", "Cerebellum", "Cerebrum", "Overlap", "Brainstem", "missing"],
            'type': 'selectbox',
            'init_value': 0,
            'add_after': ''
        },
        'Tumor size': {'values': [0, 200], 'type': 'slider', 'init_value': 38, 'add_after': ', mm'},
        'Extent of disease': {'values': ["Local", "Extensive"], 'type': 'selectbox', 'init_value': 0, 'add_after': ''},
        'Extent of resection': {
            'values': ["Gross Total resection", "Subtotal resection/Partial resection", "Partial lobectomy", "Lobectomy", "Biopsy", "Unknown"],
            'type': 'selectbox',
            'init_value': 0,
            'add_after': ''
        },
        'Radiation': {'values': ["Yes", "None/Unknown"], 'type': 'selectbox', 'init_value': 0, 'add_after': ''},
        'Chemotherapy': {'values': ["Yes", "None/Unknown"], 'type': 'selectbox', 'init_value': 0, 'add_after': ''},
    }
    
    # 将 time 加回到 input_keys
    input_keys = [
        'Diagnosis_Year',
        'Molecular_Pathology_Types',
        'Age',
        'Gender',
        'Race',
        'Marrital_status',
        'Location_of_the_tumor',
        'Tumor_size',
        'Extent_of_disease',
        'Extent_of_resection',
        'Radiation',
        'Chemotherapy',
        'time'  # 加回 time
    ]
    return settings, input_keys, level_mapping

# 更新主函数调用
settings, input_keys, level_mapping = load_setting()

@st.cache_data(show_spinner=False)
def get_model(name='DeepSurv'):
    with open('../save/DeepSurv.pkl', 'rb') as f:
        model = pickle.load(f)
    return model

def get_code():
    sidebar_code = []
    
    for key in settings:
        if settings[key]['type'] == 'slider':
            sidebar_code.append(
                "{} = st.slider('{}',{},{},key='{}')".format(
                    key.replace(' ', '____'),
                    key + settings[key]['add_after'],
                    # settings[key]['values'][0],
                    ','.join(['{}'.format(value) for value in settings[key]['values']]),
                    settings[key]['init_value'],
                    key
                )
            )
        if settings[key]['type'] == 'selectbox':
            sidebar_code.append('{} = st.selectbox("{}",({}),{},key="{}")'.format(
                key.replace(' ', '____'),
                key + settings[key]['add_after'],
                ','.join('"{}"'.format(value) for value in settings[key]['values']),
                settings[key]['init_value'],
                key
            )
            )
    return sidebar_code

if 'patients' not in st.session_state:
    st.session_state['patients'] = []
if 'display' not in st.session_state:
    st.session_state['display'] = 1
if 'model' not in st.session_state:
    st.session_state['model'] = 'DeepSurv'
deepsurv_model = get_model(st.session_state['model'])
sidebar_code = get_code()
def plot_survival():
    pd_data = pd.concat(
        [
            pd.DataFrame(
                {
                    'Survival': item['survival'],
                    'Time': item['times'],
                    'Patients': [item['No'] for i in item['times']]
                }
            ) for item in st.session_state['patients']
        ]
    )
    if st.session_state['display']:
        fig = px.line(pd_data, x="Time", y="Survival", color='Patients',range_x=[0,48], range_y=[0, 1])
    else:
        fig = px.line(pd_data.loc[pd_data['Patients'] == pd_data['Patients'].to_list()[-1], :], x="Time", y="Survival",
                      range_x=[0,48],range_y=[0, 1])
    fig.update_layout(template='simple_white',
                      title={
                          'text': 'Predicted Survival Probability',
                          'y': 0.95,
                          'x': 0.5,
                          'xanchor': 'center',
                          'yanchor': 'top',
                          'font': dict(
                              size=25
                          )
                      },
                      plot_bgcolor="white",
                      xaxis_title="Time (month)",
                      yaxis_title="Survival probability",
                      )
    st.plotly_chart(fig, use_container_width=True)

    
def plot_patients():
    patients = pd.concat(
        [
            pd.DataFrame(
                dict(
                    {
                        'Patients': [item['No']],
                        '1-Year': ["{:.2f}%".format(item['1-year'] * 100)],
                        '2-Year': ["{:.2f}%".format(item['2-year'] * 100)],
                        '3-Year': ["{:.2f}%".format(item['3-year'] * 100)]
                    },
                    **item['arg']
                )
            ) for item in st.session_state['patients']
        ]
    ).reset_index(drop=True)
    st.dataframe(patients)
def predict():
    print('update patients start . ##########')
    
    # 创建键名映射
    key_mapping = {
        'Diagnosis_Year': 'Diagnosis Year',
        'Molecular_Pathology_Types': 'Molecular Pathology Types',
        'Marrital_status': 'Marrital status',
        'Location_of_the_tumor': 'Location of the tumor',
        'Tumor_size': 'Tumor size',
        'Extent_of_disease': 'Extent of disease',
        'Extent_of_resection': 'Extent of resection'
    }
    
    # 创建反向映射
    reverse_mapping = {v: k for k, v in key_mapping.items()}
    
    input = []
    input_values = {}  # 存储用于arg的值
    
    for key in input_keys[:-1]:  # 除了最后的'time'之外的所有特征
        # 获取表单中实际使用的键名
        form_key = key_mapping.get(key, key)
        value = st.session_state[form_key]
        
        # 存储原始值用于arg
        input_values[key] = value
        
        if isinstance(value, (int, float)):  # 数值型变量
            input.append(value)
        else:  # 分类变量
            if form_key in level_mapping:
                input.append(level_mapping[form_key][value])
            else:
                input.append(value)
    
    # 添加 time 特征（从session_state获取）
    input.append(st.session_state['time'])
    input_values['time'] = st.session_state['time']
    
    # 转换为numpy数组并预测
    input_array = np.array(input).reshape(1, -1)  # 确保输入形状正确
    survival = deepsurv_model.predict_survival(input_array, t=None)
    
    data = {
        'survival': survival.flatten(),
        'times': [i for i in range(0, len(survival.flatten()))],
        'No': len(st.session_state['patients']) + 1,
        'arg': input_values,  # 使用收集的原始值
        '1-year': survival[0, 12],
        '2-year': survival[0, 24],
        '3-year': survival[0, 36]
    }
    st.session_state['patients'].append(data)
    print('update patients end ... ##########')

def plot_below_header():
    col1, col2 = st.columns([1, 9])
    col3, col4, col5, col6, col7 = st.columns([2, 2, 2, 2, 2])
    with col1:
        st.write('')
        st.write('')
        st.write('')
        st.write('')
        st.write('')
        st.write('')
        st.write('')
        st.write('')
        # st.session_state['display'] = ['Single', 'Multiple'].index(
        #     st.radio("Display", ('Single', 'Multiple'), st.session_state['display']))
        st.session_state['display'] = ['Single', 'Multiple'].index(
            st.radio("Display", ('Single', 'Multiple'), st.session_state['display']))
        # st.radio("Model", ('DeepSurv', 'NMTLR','RSF','CoxPH'), 0,key='model',on_change=predict())
    with col2:
        plot_survival()
    with col4:
        st.metric(
            label='1-Year survival probability',
            value="{:.2f}%".format(st.session_state['patients'][-1]['1-year'] * 100)
        )
    with col5:
        st.metric(
            label='2-Year survival probability',
            value="{:.2f}%".format(st.session_state['patients'][-1]['2-year'] * 100)
        )
    with col6:
        st.metric(
            label='3-Year survival probability',
            value="{:.2f}%".format(st.session_state['patients'][-1]['3-year'] * 100)
        )
    st.write('')
    st.write('')
    st.write('')
    plot_patients()
    st.write('')
    st.write('')
    st.write('')
    st.write('')
    st.write('')

st.header('DeepSurv-based model for predicting survival of Adult-type Diffuse Glioma', anchor='survival-of-Glioma')
if st.session_state['patients']:
    plot_below_header()
st.subheader("Instructions:")
st.write("1. Select patient's infomation on the left\n2. Press predict button\n3. The model will generate predictions")
st.write('***Note: this model is still a research subject, and the accuracy of the results cannot be guaranteed!***')
st.write("***[Paper link](https://www.baidu.com/)(Waiting for updates)***")
with st.sidebar:
    with st.form("my_form", clear_on_submit=False):
        # Move time input to the top of the form
        time_value = st.number_input(
            "Time from diagnosis to treatment",
            min_value=1,
            max_value=700,
            value=30,  # 默认值
            step=1,
            key="time",
            help="Enter the number of days between diagnosis and treatment (1-700 days)"
        )
        
        for code in sidebar_code:
            exec(code)
            
        col8, col9, col10 = st.columns([3, 4, 3])
        with col9:
            prediction = st.form_submit_button(
                'Predict',
                on_click=predict
            )
