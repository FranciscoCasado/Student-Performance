# Web App 
'''
Description: This program predicts the level of performance 
of a certain student, acording to their NEM, PSU score, type
of highschool, etc. using machine learning
'''

# imports

import os
import base64
import pandas as pd
from math import sqrt
import numpy as np
import streamlit as st
from joblib import load
import plotly.graph_objects as go
from cpadapter import Adapt_to_CP
import plotly.figure_factory as ff
from sklearn.metrics import mean_squared_error
from cpadapter.utils import train_cal_test_split
from sklearn.neighbors import KNeighborsRegressor
from cpadapter.performance_measures import picp, relative_mean_width


# title and subtitle
st.write("""
# 4Students
Predecir cómo le irá a un alumno en la prueba de comprensión lectora
""")
#image (no image yet)

# single or multiple inputs
single_mult = st.sidebar.selectbox(
    'Cantidad de alumnos',
    ('1', '2 o más')
)

# get data
path = (os.getcwd()+'/Data/clean_data.csv')
df = pd.read_csv(path)
df.drop(columns=['Unnamed: 0'], inplace=True)

# dictionaries used to replace categories by numbers
dict_ingreso = {0: '5% Colegios Municipalizados', 1: 'BEA: Beca Excelencia Académica', 
                2: 'Bachillerato', 3: 'Deportista Destacado', 4: 'EDT', 
                5: 'Equidad de Género', 6: 'PAA o PSU', 7: 'PACE', 8: 'Sin Información',
                9: 'SIPEE'}

dict_extablecimiento = {0: 'Extranjero', 1: 'HC Diurno', 2: 'HC Nocturno', 3: 'Municipal', 
                        4: 'Particular', 5: 'Subvencionado', 6: 'TP Comercial', 
                        7: 'TP Industrial'}

# split the data into training, calibration and test sets
data = train_cal_test_split(df, 'PORCENTAJE DE LOGRO', 0.7, 0.2, True)
x_train = data[0]
y_train = data[1]
x_cal = data[2]
y_cal = data[3]
x_test = data[4]
y_test = data[5]

# get feature input from the user
def get_user_input_single():
    nem = st.slider('Puntaje NEM', 150, 850, 500)
    psu_len = st.slider('Puntaje PSU Lenguaje', 150, 850, 500)
    ing = st.selectbox(
        'Tipo de ingreso',
        ('5% Colegios Municipalizados', 'BEA: Beca Excelencia Académica',
        'Bachillerato', 'Deportista Destacado', 'EDT',
        'Equidad de Género', 'PAA o PSU', 'PACE', 'Sin Información', 'SIPEE')
        )
    est = st.selectbox(
        'Tipo de Establecimeinto',
        ('Extranjero', 'HC Diurno', 'HC Nocturno', 'Municipal',
        'Particular', 'Subvencionado', 'TP Comercial', 'TP Industrial')
        )
    # change tipo_ingreso to the numeric value
    ing_vals = list(dict_ingreso.values())
    ing_keys = list(dict_ingreso.keys())
    ing_tipo = ing_keys[ing_vals.index(ing)]
    # cange tipo_establecimiento to the numeric value
    est_vals = list(dict_extablecimiento.values())
    est_keys = list(dict_extablecimiento.keys())
    est_tipo = est_keys[est_vals.index(est)]

    # user data
    user_data = {
        'TIPO DE ESTABLECIMIENTO': est_tipo,
        'NEM': nem,
        'PSU LENGUAJE': psu_len,
        'VIA DE INGRESO': ing_tipo
    }
    return pd.DataFrame(user_data, index=[0])

def get_user_input_mult():
    mult_text = (
        'Se debe entregar un archivo CSV con las siguientes columnas:'
        'Tipo de Establecimiento, NEM, Puntaje PSU Lenguaje y Vía de'
        'ingreso, en este orden.'
        ' Las columnas no deben tener acentos'
        ' Las opciones de las variables categóricas se pueden ver en el'
        'ingreso de datos de un estidiante en particular. Hay que respetar letras'
        'mayúsculas y acentos.\n'
        'No ingresar datos vacíos, ni elementos identificadores de los alumnos,'
        'para identificarlos se usará el índice.'
    )
    datos = st.file_uploader('Datos de los alumons', type='csv')
    if datos is not None:
        df_input = pd.read_csv(datos)
        df_input.columns = df_input.columns.str.lower()
        new_establecimiento = dict([(value, key) for key, value in dict_extablecimiento.items()])
        new_ingreso = dict([(value, key) for key, value in dict_ingreso.items()])
        df_input['tipo de establecimiento'].replace(new_establecimiento, inplace=True)
        df_input['via de ingreso'].replace(new_ingreso, inplace=True)
        return df_input
    else:
        return pd.DataFrame()

# Create and train ML model
kn = load(os.getcwd()+'/web_app/knneighbors.joblib')
adapted_kn = Adapt_to_CP(kn, True)

# Show models metrics
prediction_kn = adapted_kn.calibrate_and_predict(x_cal, y_cal, x_test, 0.8)
lb_kn = prediction_kn[0]
pred_kn = prediction_kn[1]
ub_kn = prediction_kn[2]
st.subheader('Error promedio del modelo predictivo:')
error = sqrt(mean_squared_error(y_test, pred_kn)) * 100
st.write(str(round(error, 2)) + '%')
st.subheader('Cobertura empírica del intervalo de confianza:')
st.write(str(round(picp(y_test, lb_kn, ub_kn), 2) * 100) + '%')
st.subheader('Ancho promedio del intervalo con respecto al porcentaje de logro promedio')
st.write(str(round(relative_mean_width(y_test, lb_kn, ub_kn), 2) * 100) + '%')


# predict users input
if single_mult == '1':
    user_features = get_user_input_single()
else:
    user_features = get_user_input_mult()
#
if user_features.empty:
    st.write('Aún no se han ingresado datos')
else:
    st.subheader('Datos ingresados de los estudiantes:')
    st.write(user_features.head())
    preds_user = adapted_kn.predict(user_features.values, 0.8)
    lb_user = preds_user[0]
    pred_user = preds_user[1]
    ub_user = preds_user[2]

# # display the students prediction
if single_mult == '1':
    st.subheader('Porcentaje de logro predicho:')
    st.write(str(round(pred_user[0] * 100, 2)) + '%')
    st.subheader('Límite inferior predicho:')
    st.write(str(round(lb_user[0]* 100, 2)) + '%')
    st.subheader('Límite superior predicho:')
    st.write(str(round(ub_user[0]* 100, 2)) + '%')
else:
    if not user_features.empty:
        user_features['prediccion de logro'] = np.around(pred_user*100, 2)
        user_features['limite inferior'] = np.around(lb_user*100, 2)
        user_features['limite superior'] = np.around(ub_user*100, 2)
# Test Plot
if single_mult == '1':
    fig = go.Figure(data=[go.Surface(z=np.random.rand(30,20))])
    fig.update_layout(title='Plot Prueba', autosize=False,
                    width=800, height=800,
                    margin=dict(l=40, r=40, b=40, t=40))
    st.plotly_chart(fig)
else:
    if not user_features.empty:
        # fig = ff.create_distplot(
        #     user_features['prediccion de logro'],
        #     'desempeño predicho'
        # )
        # st.plotly_chart(fig, user_container_width=True)
        # Download Results
        def get_table_download_link(df):
            csv = df.to_csv(index=False)
            b64 = base64.b64encode(csv.encode()).decode()  
            href = f'<a href="data:file/csv;base64,{b64}" download="Resultados.csv">Descargar Resultados</a>'
            return href

        st.markdown(get_table_download_link(user_features), unsafe_allow_html=True)