
import logging
from logging.handlers import RotatingFileHandler
from typing import Dict

from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )

#-----------------------------------------------
#-------- Librerias Telegram  ------------------
#-----------------------------------------------
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackContext,
    ContextTypes,
)

from datetime import datetime
import numpy as np
import os, socket, time
from decimal import Decimal
import pandas as pd
 
from db_pool import Database
#-----------------------------------------------
#--------- FIN declaración de Librerias --------
#-----------------------------------------------
# Enable logging
archivo_actual=os.path.basename(__file__).replace('.py','')
ArchivoLog=f'/var/log/{archivo_actual}.log'

handler=RotatingFileHandler(ArchivoLog, maxBytes=10*1024*1024, backupCount=5)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", handlers=[handler], level=logging.DEBUG
)
logger = logging.getLogger(__name__)

#-----------------------------------------------
#----------Creación de Pool de conexiones ------
# ----------- para la base de datos-------------
#-----------------------------------------------
directorio_actual=os.getcwd()
hostName=socket.gethostname()

if hostName =='vps-4406360-x':
    db_host='localhost'
    db_user='crm'
    db_password='aquelaLRC31772.'
    pool_size=3
else:
    db_host='10.10.98.14'
    #db_host='149.50.134.164'
    db_user='crm'
    db_password='aquelaLRC31772.'
    pool_size=3
db_database='crm'
db_port=3306

# creo la instancia de la base de datos
db= Database(db_user=db_user, db_password=db_password, db_host=db_host, db_database=db_database, db_port=db_port, pool_size=pool_size)


#-----------------------------------------------
#---------Fin de la creación del pool DB--------
#-----------------------------------------------
RegEx=''
#---------- Archivo de Configuración -----------


SQL_parametros='SELECT parametro, valor from cat_parametros WHERE bot_id=1;'

df_parametros=db.ejecutar_consulta(consulta=SQL_parametros, columns=['parametro', 'valor'])

# TOKEN Pruebas es "tokenp" 
if hostName == 'vps-4406360-x':
    TOKEN=df_parametros[df_parametros['parametro']=='TOKEN']['valor'].values[0]
    PATH_FOTO=df_parametros[df_parametros['parametro']=='PATH_FOTO_TICKET']['valor'].values[0]
else:
    TOKEN=df_parametros[df_parametros['parametro']=='TOKEN_D']['valor'].values[0]
    PATH_FOTO=df_parametros[df_parametros['parametro']=='PATH_FOTO_TICKET_D']['valor'].values[0]

#-------- Variables Globales

START, VALIDAR_AHORA, MENU_PRINCIPAL, TICKET, FOTO, DEPARTAMENTOS, T_ABIERTOS, T_A_COMENTAR, T_A_DETALLE, T_A_CAMBIOESTATUS, T_ASIGNADOS, ASI_SELECCIONA, ASI_CAMBIOESTATUS, ASI_COMENTAR, ASI_DB_ESTATUS, VALIDAR_CIERRE, VAL_VAL_REABRIR, REA_FOTO, SLA = range(19)

# ------ Variable para identificar si el flujo entro en la funcion: "nombre"
reply_SiNo = [
    ["Si", "No"],
]
markupSiNo = ReplyKeyboardMarkup(reply_SiNo, one_time_keyboard=True)

reply_Ok = [
    ["Ok"],
]
markupOk = ReplyKeyboardMarkup(reply_Ok, one_time_keyboard=True)

reply_Actualizar = [
    ["Actualizar"],
]
markupActualizar = ReplyKeyboardMarkup(reply_Actualizar, one_time_keyboard=True)

reply_CCR = [
    ["Cambiar Estatus","Comentar","Re-Asignar"],
]
markupCCR = ReplyKeyboardMarkup(reply_CCR, one_time_keyboard=True)

reply_CC = [
    ["Cambiar Estatus","Comentar"],
]
markupCC = ReplyKeyboardMarkup(reply_CC, one_time_keyboard=True)

reply_NAAV = [
    ["Nuevo","Abiertos","Asignados","Validar"],
]
markupNAAV = ReplyKeyboardMarkup(reply_NAAV, one_time_keyboard=True)

reply_NAb = [
    ["Nuevo","Abiertos"],
]
markupNAb = ReplyKeyboardMarkup(reply_NAb, one_time_keyboard=True)

reply_NAbAs = [
    ["Nuevo","Abiertos","Asignados"],
]
markupNAbAs = ReplyKeyboardMarkup(reply_NAbAs, one_time_keyboard=True)

reply_NAbV = [
    ["Nuevo","Abiertos","Validar"],
]
markupNAbV = ReplyKeyboardMarkup(reply_NAbV, one_time_keyboard=True)

reply_NAs= [
    ["Nuevo","Asignados"],
]
markupNAs = ReplyKeyboardMarkup(reply_NAs, one_time_keyboard=True)

reply_NAsV = [
    ["Nuevo","Asignados","Validar"],
]
markupNAsV = ReplyKeyboardMarkup(reply_NAsV, one_time_keyboard=True)

reply_NV = [
    ["Nuevo","Validar"],
]
markupNV = ReplyKeyboardMarkup(reply_NV, one_time_keyboard=True)

reply_N = [
    ["Nuevo"],
]
markupN = ReplyKeyboardMarkup(reply_N, one_time_keyboard=True)

reply_ValidadoReAbrir = [
    ["Validado","Re Abrir"],
]
markupValidadoReAbrir = ReplyKeyboardMarkup(reply_ValidadoReAbrir, one_time_keyboard=True)

reply_Cancelar = [
    ["Cancelar"],
]
markupCancelar = ReplyKeyboardMarkup(reply_Cancelar, one_time_keyboard=True)


#--------------------------------------------------------------------------
#-------------------- Check List Inicial. -----------------
#--------------------------------------------------------------------------

def facts_to_str(user_data: Dict[str, str]) -> str:
    """Helper function for formatting the gathered user info."""
    facts = [f"{key} - {value}" for key, value in user_data.items()]
    return "\n".join(facts).join(["\n", "\n"])

async def start(update: Update, context: CallbackContext) -> int:
    """Start the conversation and ask user for input."""
    user = update.message.from_user

    context.user_data[update.effective_chat.id]={}
    context.user_data[update.effective_chat.id]['chat_id']=update.effective_chat.id,
    context.user_data[update.effective_chat.id]['ticket_id']=0,
    context.user_data[update.effective_chat.id]['name']=user.full_name,
    context.user_data[update.effective_chat.id]['username']=update.message.from_user.name,
    context.user_data[update.effective_chat.id]['departamento_id']=''
    context.user_data[update.effective_chat.id]['asignado_a']=''
    context.user_data[update.effective_chat.id]['descripcion']=''
    context.user_data[update.effective_chat.id]['imagen']='Sin Imagen'
    context.user_data[update.effective_chat.id]['status_id']='1'
    context.user_data[update.effective_chat.id]['sla_id']='4'
    context.user_data[update.effective_chat.id]['path_foto']=PATH_FOTO
    
    print(context.user_data[update.effective_chat.id])


    SQL_asignado=f'SELECT count(ticket_id) as Asignados FROM crm.tele_tickets WHERE estatus_id != 4 AND asignado_a = "{context.user_data[update.effective_chat.id]["username"][0]}";'
    df_t_asignados=db.ejecutar_consulta(consulta=SQL_asignado, columns=['Asignados'])
    
    SQL_abierto=f'SELECT count(ticket_id) as Abiertos FROM crm.tele_tickets WHERE estatus_id != 4 AND username = "{context.user_data[update.effective_chat.id]["username"][0]}";'
    df_t_abiertos=db.ejecutar_consulta(consulta=SQL_abierto, columns=['Abiertos'])

    SQL_validar=f'SELECT count(ticket_id) as "Por validar" FROM crm.tele_tickets WHERE estatus_id = 4 AND validado = 0 AND username = "{context.user_data[update.effective_chat.id]["username"][0]}";'
    df_t_validar=db.ejecutar_consulta(consulta=SQL_validar, columns=['Por Validar'])

    mensaje='Concentradora de Residuos Solidos\n\n'\
            'Aplicación para el reporte de tickets\n\n'
    
    NAbiertos=int(df_t_abiertos.loc[0, 'Abiertos'])
    NAsignados=int(df_t_asignados.loc[0, 'Asignados'])
    NAValidar=int(df_t_validar.loc[0, 'Por Validar'])

    if NAValidar>0:
        mensaje=f'Usted tiene: {NAValidar}, tickets por validar,\n\n'\
                '¿Puede validarlos ahora?'
        await update.message.reply_text(mensaje, reply_markup=markupSiNo)
        return VALIDAR_AHORA

    if not df_t_abiertos.empty:
        mensaje = mensaje + f'Abiertos: {NAbiertos}\n\n'
    if not df_t_asignados.empty:
        mensaje = mensaje + f'Asignados: {NAsignados}\n\n'
    if not df_t_validar.empty:
        mensaje = mensaje + f'Por validar: {NAValidar}\n\n'       

    mensaje = mensaje + 'Por favor seleccione una accion a realizar:'

    if NAbiertos  > 0 and  NAsignados  ==  0 and  NAValidar  ==  0:
        await update.message.reply_text(mensaje, reply_markup=markupNAb)
    elif NAbiertos  > 0 and  NAsignados  >  0 and  NAValidar  ==  0:
        await update.message.reply_text(mensaje, reply_markup=markupNAbAs)
    elif NAbiertos  > 0 and NAsignados  ==  0 and  NAValidar  >  0:
        await update.message.reply_text(mensaje, reply_markup=markupNAbV)
    elif NAbiertos  == 0 and  NAsignados  >  0 and  NAValidar  ==  0:
        await update.message.reply_text(mensaje, reply_markup=markupNAs)
    elif NAbiertos  ==  0 and  NAsignados  >  0 and  NAValidar  ==  0:
        await update.message.reply_text(mensaje, reply_markup=markupNAsV)
    elif NAbiertos  ==  0 and NAsignados  ==  0 and  NAValidar  >  0:
        await update.message.reply_text(mensaje, reply_markup=markupNV)
    elif NAbiertos  ==  0 and NAsignados  ==  0 and  NAValidar  ==  0:
        await update.message.reply_text(mensaje, reply_markup=markupN)
    else:
        await update.message.reply_text(mensaje, reply_markup=markupNAAV)

    return MENU_PRINCIPAL

#-------------------------------------------------------
#-------------------------------------------------------
#-------------------------------------------------------
#                 Programa Nuevos
#-------------------------------------------------------
#-------------------------------------------------------
#-------------------------------------------------------

async def departamentos(update: Update, context: CallbackContext) -> int:
    global df_dep

    SQL='SELECT departamento_id as ID, nombre as Departamento FROM cat_departamentos ORDER BY nombre'
    df_dep=db.ejecutar_consulta(consulta=SQL, columns=['ID', 'Departamento'])

    mensaje = 'A que area será asignado el reporte?:\n\n'\
            f'{df_dep["Departamento"].to_string()}'

    await update.message.reply_text(mensaje)

    return DEPARTAMENTOS

async def ticket(update: Update, context: CallbackContext) -> int:

    if update.message.text.isdigit():
        if int(update.message.text) > int(len(df_dep))-1:
            mensaje='Por favor solo digite un número de la relación de departamentos:\n\n'\
                    f'{df_dep["Departamento"].to_string()}'
            
            await update.message.reply_text(mensaje)

            return DEPARTAMENTOS
        else:
            context.user_data[update.effective_chat.id]['departamento_id']=int(df_dep.loc[int(update.message.text),'ID'])


    mensaje="Por favor describa el reporte:"
    
    await update.message.reply_text(mensaje)

    return TICKET

async def foto(update: Update, context: CallbackContext) -> int:

    if update.message.text != 'Si': 
        context.user_data[update.effective_chat.id]['descripcion']=update.message.text
        mensaje='Requiere tomar una foto al objeto reportado?'
    elif update.message.text == 'Si':
            
        mensaje='Por favor, Tome la foto.'
    
    await update.message.reply_text(mensaje, reply_markup=markupSiNo)
    
    return FOTO
    
async def sla(update: Update, context: CallbackContext) -> int:
    global df_sla

    foto_file = await update.message.photo[-1].get_file()
    dir_archivo=f'{PATH_FOTO}{foto_file.file_unique_id}.jpg'
    await foto_file.download_to_drive(dir_archivo)
    context.user_data[update.effective_chat.id]['imagen']=f'{foto_file.file_unique_id}.jpg'
    
    #--------------- Fin Foto ---------------------------



    SQL='SELECT sla_id as ID, nombre as Prioridad, dias as Días FROM cat_sla ORDER BY sla_id'
    df_sla=db.ejecutar_consulta(consulta=SQL, columns=['ID', 'Prioridad', 'Días'])

    mensaje='Por favor seleccione la prioridad.\n\n'\
            'De la siguiente lista, seleccione el ID del SLA:\n\n'\
            f'{df_sla.to_string(index=False)}'

    await update.message.reply_text(mensaje)
        
    return SLA

async def slaSF(update: Update, context: CallbackContext) -> int:
    global df_sla

    SQL='SELECT sla_id as ID, nombre as Prioridad, dias as Días FROM cat_sla ORDER BY sla_id'
    df_sla=db.ejecutar_consulta(consulta=SQL, columns=['ID', 'Prioridad', 'Días'])

    mensaje='Por favor seleccione la prioridad.\n\n'\
            'De la siguiente lista, seleccione el ID del tiempo esperado de respuesta:\n\n'\
            f'{df_sla.to_string(index=False)}'

    await update.message.reply_text(mensaje)
        
    return SLA

async def despedida(update: Update, context: CallbackContext) -> int:

    if update.message.text.isdigit():
        if int(update.message.text) > int(len(df_sla))-1:
            mensaje='Por favor solo digite un número de la relación de prioridad:\n\n'\
                    f'{df_sla.to_string(index=False)}'
            await update.message.reply_text(mensaje)

            return SLA
        else:
            context.user_data[update.effective_chat.id]['sla_id']=update.message.text

    SQL = f"SELECT username from cat_user WHERE posicion = 'Responsable' AND departamento_id = '{context.user_data[update.effective_chat.id]['departamento_id']}';"
    df_resp = db.ejecutar_consulta(consulta=SQL, columns=['username'])

    context.user_data[update.effective_chat.id]['asignado_a']=df_resp.loc[0,'username'] 

    SQL='INSERT INTO crm.tele_tickets (username, departamento_id, asignado_a, descripcion, imagen, estatus_id, sla_id) VALUES ('\
        f'"{context.user_data[update.effective_chat.id]["username"][0]}", '\
        f'"{context.user_data[update.effective_chat.id]["departamento_id"]}", '\
        f'"{context.user_data[update.effective_chat.id]["asignado_a"]}", '\
        f'"{context.user_data[update.effective_chat.id]["descripcion"]}", '\
        f'"{context.user_data[update.effective_chat.id]["imagen"]}", '\
        f'"{context.user_data[update.effective_chat.id]["status_id"]}", '\
        f'"{context.user_data[update.effective_chat.id]["sla_id"]}"'\
        ');'
    
    db.ejecutar_actualizacion(SQL)
    
    #SQL=f'SELECT max(ticket_id) as Ticket FROM crm.tele_tickets WHERE departamento_id = "{context.user_data[update.effective_chat.id]["departamento_id"]}";'

    SQL='SELECT concat(substring(cd.nombre, 1 ,3), "-", max(tt.ticket_id)) as Ticket '\
        'FROM (tele_tickets tt JOIN cat_departamentos cd ON (tt.departamento_id = cd.departamento_id))'\
        f'WHERE tt.departamento_id = "{context.user_data[update.effective_chat.id]["departamento_id"]}"'\
        'group by cd.nombre'


    df_ticket_id = db.ejecutar_consulta(consulta=SQL, columns=['Ticket'])

    mensaje='Su reporte fue recibido.\n'\
            f'Su numero de ticket es: {df_ticket_id.loc[0, "Ticket"]}'

    await update.message.reply_text(mensaje, reply_markup=markupOk)
    return ConversationHandler.END

async def caracterInvalido(update: Update, context: CallbackContext) -> int:
    mensaje=f'''En su última captura digito un caracter invalido, debe comenzar de nuevo.

    Usted digitó: "{update.message.text}"
    '''
    await update.message.reply_text(mensaje, reply_markup=ReplyKeyboardRemove()) 
    
    context.user_data[update.effective_chat.id]={}
    return ConversationHandler.END
    
    #-------------------------  Insertar en Base de Datos y Obtener Numero de Ticket

#-------------------------------------------------------
#-------------------------------------------------------
#-------------------------------------------------------
#                 Programa Abiertos
#-------------------------------------------------------
#-------------------------------------------------------
#-------------------------------------------------------

async def t_abiertos(update: Update, context: CallbackContext) -> int:
    global df_t_abiertos
    SQL='SELECT tt.ticket_id as Ticket, tt.descripcion as Descripción, ce.nombre as Estatus, departamento_id '\
        'FROM (tele_tickets tt JOIN cat_estatus ce ON (tt.estatus_id = ce.estatus_id)) '\
        f'WHERE tt.estatus_id != 4 AND username = "{context.user_data[update.effective_chat.id]["username"][0]}"'
    
    df_t_abiertos=db.ejecutar_consulta(consulta=SQL, columns=['Ticket', 'Descripción', 'Estatus', 'departamento_id'])
    df_t_abiertos_lim=df_t_abiertos[['Ticket', 'Descripción', 'Estatus']]
    mensaje='Esta es la lista de tickets abiertos:\n\n'\
            f'{df_t_abiertos_lim.to_string(index=False)}\n\n'\
            'Por favor digite el ID del ticket con el que desea trabajar:'
    
    await update.message.reply_text(mensaje, reply_markup=markupOk )

    return T_ABIERTOS

async def t_a_detalle(update: Update, context: CallbackContext) -> int:
    global df_ticket
    esDigito=update.message.text
    if esDigito.isdigit():
        if  bool((df_t_abiertos['Ticket']==int(update.message.text)).any()):

            context.user_data[update.effective_chat.id]["departamento_id"]=int(df_t_abiertos['departamento_id'][0])

            SQL='SELECT ticket_id as ID, cuUSER.nombre as Solicita, tt.descripcion as Descripción, ce.nombre as Estatus, DATEDIFF(CURDATE(), tt.fecha) AS "Días Abierto", tt.fecha AS Solicitado, csla.nombre as Prioridad, date_add(date_format(tt.fecha, "%d-%m-%y"), interval csla.dias DAY) AS "Fecha de Entrega", DATEDIFF(CURDATE(), date_add(tt.fecha, interval csla.dias DAY)) AS "Días Vencido" '\
                'FROM (tele_tickets tt '\
                'JOIN cat_estatus ce ON (tt.estatus_id = ce.estatus_id) '\
                'JOIN cat_user cuUSER ON (tt.username=cuUSER.username) '\
                'JOIN cat_sla csla ON (tt.sla_id=csla.sla_id)) '\
                f'WHERE tt.ticket_id={update.message.text} '\
                f'AND tt.departamento_id={context.user_data[update.effective_chat.id]["departamento_id"]}'
            df_ticket=db.ejecutar_consulta(consulta=SQL, columns=["ID", "Solicita", "Descripción", "Estatus", "Días Abierto", "Solicitado", "Prioridad", "Fecha de Entrega", "Días Vencido"])

            SQL=f'SELECT ticket_id, asignado_a, departamento_id, descripcion, imagen, estatus_id FROM tele_tickets WHERE ticket_id={update.message.text} AND departamento_id={context.user_data[update.effective_chat.id]["departamento_id"]}'
            df_ticket_2=db.ejecutar_consulta(consulta=SQL, columns=['ticket_id', 'asignado_a', 'departamento_id', 'descripcion', 'imagen', 'estatus_id'])

            context.user_data[update.effective_chat.id]['ticket_id']=int(df_ticket_2['ticket_id'][0])
            context.user_data[update.effective_chat.id]['descripcion']=df_ticket_2['descripcion'][0]
            context.user_data[update.effective_chat.id]['imagen']=df_ticket_2['imagen'][0]
            context.user_data[update.effective_chat.id]['status_id']=int(df_ticket_2['estatus_id'][0])
            context.user_data[update.effective_chat.id]['asignado_a']=df_ticket_2['asignado_a'][0]

            SQL='SELECT ta.avances_id as ITEM, substr(ta.descripcion,1,20) AS DescripciónC, ta.descripcion AS Descripción, ta.fecha as Fecha, ce.nombre as Estatus '\
                'FROM (tickets_avances ta JOIN cat_estatus ce ON(ta.estatus_id=ce.estatus_id)) '\
                f'WHERE ta.ticket_id = {context.user_data[update.effective_chat.id]["ticket_id"]} '\
                f'AND ta.departamento_id = {context.user_data[update.effective_chat.id]["departamento_id"]} '\
                'ORDER BY ta.ticket_id, ta.avances_id;'
            
            df_ticket_avances=db.ejecutar_consulta(consulta=SQL, columns=['ITEM', 'DescripciónC', 'Descripción', 'Fecha', 'Estatus'])
            df_ticket_avances_lim=df_ticket_avances[['ITEM', 'DescripciónC', 'Fecha', 'Estatus']]

            mensaje='Este ticket tiene la siguiente información:\n\n'\
                        f'{df_ticket.T.to_string(header=False)}\n\n'
            if not df_ticket_avances_lim.empty:
                mensaje=mensaje+'Con los siguientes comentarios\n\n'\
                        f'{df_ticket_avances_lim.to_string(index=False)}\n\n'\
                        'Si desea ver el detalle de algún comentario digite el ITEM. \n\n'
            else:
                mensaje=mensaje+'Este ticket aun no tiene comentarios.\n\n'
            
            mensaje=mensaje+'Seleccione la actividad que va a realizar:'
            # ------------------- Colocar la condición si es responsable de area puede reasignar
            # ------------------- Este valor lo tomamos de la tabla cat_usuer
            SQL=f'SELECT count(*) as Responsable FROM crm.cat_user WHERE posicion= "Responsable" AND username = "{context.user_data[update.effective_chat.id]["username"][0]}"'
            df_resp=db.ejecutar_consulta(consulta=SQL, columns=['Responsable'])
            if bool(df_resp['Responsable'][0]):
                await update.message.reply_text(mensaje, reply_markup=markupCCR)
            else:
                await update.message.reply_text(mensaje, reply_markup=markupCC)
            
            return T_A_COMENTAR
        else:
            mensaje='Debe escojer un ID Valido:\n'\
                    'Por favor intente de nuevo'
            await update.message.reply_text(mensaje, reply_markup=markupOk)
            return T_ABIERTOS
    else:
        mensaje='Debe escojer un ID Valido:\n'\
                'Por favor intente de nuevo'
        await update.message.reply_text(mensaje, reply_markup=markupOk)
        return T_ABIERTOS

async def t_a_comentar(update: Update, context: CallbackContext) -> int:
    
    mensaje='Por favor ingrese el comentario sobre el avance del ticket:'

    await update.message.reply_text(mensaje, reply_markup=markupCancelar)

    return T_A_COMENTAR

async def t_a_cambiarEstatus(update: Update, context: CallbackContext) -> int:
    ...

async def t_a_db(update: Update, context: CallbackContext) -> int:
    
    SQL='INSERT INTO tickets_avances (ticket_id, departamento_id, asignado_a, descripcion, imagen, estatus_id) VALUES ('\
        f'{context.user_data[update.effective_chat.id]["ticket_id"]}, '\
        f'"{context.user_data[update.effective_chat.id]["departamento_id"]}", '\
        f'"{context.user_data[update.effective_chat.id]["asignado_a"]}", '\
        f'"{update.message.text}", '\
        f'"{context.user_data[update.effective_chat.id]["imagen"]}", '\
        f'{context.user_data[update.effective_chat.id]["status_id"]})'

    db.ejecutar_actualizacion(consulta=SQL)

    mensaje='El ticket se actulizó con éxito!!'

    await update.message.reply_text(mensaje, reply_markup=markupOk)

    return ConversationHandler.END

#-------------------------------------------------------
#-------------------------------------------------------
#-------------------------------------------------------
#                 Programa Asignados
#-------------------------------------------------------
#-------------------------------------------------------
#-------------------------------------------------------

async def t_asignados(update: Update, context: CallbackContext) -> int: 
    global df_t_asignados
    
    SQL='SELECT ticket_id as Ticket, substr(descripcion, 1,10) as Descripción, ce.nombre as Estatus, departamento_id '\
        'FROM (tele_tickets tt JOIN cat_estatus ce ON (tt.estatus_id = ce.estatus_id)) '\
        f'WHERE tt.estatus_id != 4 AND tt.asignado_a = "{context.user_data[update.effective_chat.id]["username"][0]}";'
    
    df_t_asignados=db.ejecutar_consulta(consulta=SQL, columns=['Ticket', 'Descripción', 'Estatus', 'departamento_id'])
    context.user_data[update.effective_chat.id]['departamento_id']=int(df_t_asignados['departamento_id'][0])
    df_t_asignados_lim=df_t_asignados[['Ticket', 'Descripción', 'Estatus']]

    if df_t_asignados.empty:
        mensaje='No tiene Tickets asignados.'
    else:
        mensaje='Esta es la lista de tickets que tiene asignados:\n\n'\
                f'{df_t_asignados_lim.to_string(index=False)}\n\n'\
                'Por Favor digite el indice del ticket con el que desea Trabajar'
    
    await update.message.reply_text(mensaje, reply_markup=markupActualizar)

    return T_ASIGNADOS

async def asi_asignado(update: Update, context: CallbackContext) -> int:
    global df_ticket
    esDigito=update.message.text
    if esDigito.isdigit():
        if  bool((df_t_asignados['Ticket']==int(update.message.text)).any()):
            SQL='SELECT ticket_id as ID, cuUSER.nombre as Solicita, tt.descripcion as Descripción, ce.nombre as Estatus, DATEDIFF(CURDATE(), tt.fecha) AS "Días Abierto", tt.fecha AS Solicitado, csla.nombre as Prioridad, date_add(date_format(tt.fecha, "%d-%m-%y"), interval csla.dias DAY) AS "Fecha de Entrega", DATEDIFF(CURDATE(), date_add(tt.fecha, interval csla.dias DAY)) AS "Días Vencido" '\
                'FROM (tele_tickets tt '\
                'JOIN cat_estatus ce ON (tt.estatus_id = ce.estatus_id) '\
                'JOIN cat_user cuUSER ON (tt.username=cuUSER.username) '\
                'JOIN cat_sla csla ON (tt.sla_id=csla.sla_id)) '\
                f'WHERE tt.ticket_id={update.message.text} '\
                f'AND tt.departamento_id={context.user_data[update.effective_chat.id]["departamento_id"]}'
            df_ticket=db.ejecutar_consulta(consulta=SQL, columns=["ID", "Solicita", "Descripción", "Estatus", "Días Abierto", "Solicitado", "Prioridad", "Fecha de Entrega", "Días Vencido"])

            SQL=f'SELECT ticket_id, asignado_a, departamento_id, descripcion, imagen, estatus_id FROM tele_tickets WHERE ticket_id="{update.message.text}" AND departamento_id={context.user_data[update.effective_chat.id]["departamento_id"]}'
            df_ticket_2=db.ejecutar_consulta(consulta=SQL, columns=['ticket_id', 'asignado_a', 'departamento_id', 'descripcion', 'imagen', 'estatus_id'])

            context.user_data[update.effective_chat.id]['ticket_id']=int(df_ticket_2['ticket_id'][0])
            context.user_data[update.effective_chat.id]['descripcion']=df_ticket_2['descripcion'][0]
            context.user_data[update.effective_chat.id]['imagen']=df_ticket_2['imagen'][0]
            context.user_data[update.effective_chat.id]['status_id']=int(df_ticket_2['estatus_id'][0])
            context.user_data[update.effective_chat.id]['asignado_a']=df_ticket_2['asignado_a'][0]

            SQL='SELECT ta.avances_id as ITEM, substr(ta.descripcion,1,20) AS DescripciónC, ta.descripcion AS Descripción, ta.fecha as Fecha, ce.nombre as Estatus '\
                'FROM (tickets_avances ta JOIN cat_estatus ce ON(ta.estatus_id=ce.estatus_id)) '\
                f'WHERE ta.ticket_id = {context.user_data[update.effective_chat.id]["ticket_id"]} '\
                f'AND ta.departamento_id = {context.user_data[update.effective_chat.id]["departamento_id"]} '\
                'ORDER BY ta.ticket_id, ta.avances_id;'
            
            df_ticket_avances=db.ejecutar_consulta(consulta=SQL, columns=['ITEM', 'DescripciónC', 'Descripción', 'Fecha', 'Estatus'])
            df_ticket_avances_lim=df_ticket_avances[['ITEM', 'DescripciónC', 'Fecha', 'Estatus']]

            mensaje='Este ticket tiene la siguiente información:\n\n'\
                        f'{df_ticket.T.to_string(header=False)}\n\n'
            if not df_ticket_avances_lim.empty:
                mensaje=mensaje+'Con los siguientes comentarios\n\n'\
                        f'{df_ticket_avances_lim.to_string(index=False)}\n\n'\
                        'Si desea ver el detalle de algún comentario digite el ITEM. \n\n'
            else:
                mensaje=mensaje+'Este ticket aun no tiene comentarios.\n\n'
            
            mensaje=mensaje+'Seleccione la actividad que va a realizar:'
        
            # ------------------- Colocar la condición si es responsable de area puede reasignar
            # ------------------- Este valor lo tomamos de la tabla cat_usuer
            SQL=f'SELECT count(*) as Responsable FROM crm.cat_user WHERE posicion= "Responsable" AND username = "{context.user_data[update.effective_chat.id]["username"][0]}"'
            df_resp=db.ejecutar_consulta(consulta=SQL, columns=['Responsable'])
            if bool(df_resp['Responsable'][0]):
                await update.message.reply_text(mensaje, reply_markup=markupCCR)
            else:
                await update.message.reply_text(mensaje, reply_markup=markupCC)
            
            return ASI_SELECCIONA
        else:
            mensaje='Debe escojer un ID Valido y Asignado:\n'\
                    'Por favor intente de nuevo'
            await update.message.reply_text(mensaje, reply_markup=markupOk)
            return ASI_SELECCIONA    
    else:
        mensaje='Debe escojer un ID Valido y Asignado:\n'\
                'Por favor intente de nuevo'
        await update.message.reply_text(mensaje, reply_markup=markupOk)
        return ASI_SELECCIONA

async def asi_cambioEstatus(update: Update, context: CallbackContext) -> int:    
    global df_estatus

    SQL='SELECT estatus_id AS ID, nombre AS Estatus FROM crm.cat_estatus ORDER BY estatus_id;'
    df_estatus=db.ejecutar_consulta(consulta=SQL, columns=['ID', 'Estatus'])

    mensaje='Por favor ingrese el ID del nuevo estatus:\n\n'
    if context.user_data[update.effective_chat.id]['status_id']==5:
        mensaje = mensaje + '4 Cerrado\n\n'\
        'Si el ticket fué Re-abierto, solo puede ser Cerrado.\n\n'
    else:
        mensaje = mensaje + f'{df_estatus.to_string(index=False)}\n\n'

    mensaje = mensaje + 'Por favor digite el ID del nuevo estatus.'
    await update.message.reply_text(mensaje)
    return ASI_CAMBIOESTATUS

async def asi_bd_Estatus(update: Update, context: CallbackContext) -> int:    

    SQL_update=f'UPDATE tele_tickets SET estatus_id = {update.message.text} WHERE ticket_id={df_ticket["ID"][0]}'
    SQL_insert='INSERT INTO tickets_avances (ticket_id, departamento_id, asignado_a, descripcion, imagen, estatus_id) VALUES ('\
                f'{context.user_data[update.effective_chat.id]["ticket_id"]}, '\
                f'"{context.user_data[update.effective_chat.id]["departamento_id"]}", '\
                f'"{context.user_data[update.effective_chat.id]["asignado_a"]}", '\
                f'"{context.user_data[update.effective_chat.id]["descripcion"]}", '\
                f'"{context.user_data[update.effective_chat.id]["imagen"]}", '\
                f'{context.user_data[update.effective_chat.id]["status_id"]})'

    db.ejecutar_actualizacion(consulta=SQL_update)
    db.ejecutar_actualizacion(consulta=SQL_insert)

    mensaje='El cambio de estatus se realizó correctamente.'

    await update.message.reply_text(mensaje, reply_markup=markupOk)

    return ConversationHandler.END

async def asi_cambioEComentario(update: Update, context: CallbackContext) -> int:    

    if  bool((df_estatus['ID']==int(update.message.text)).any()):
        context.user_data[update.effective_chat.id]['status_id']=update.message.text
    else:
        mensaje='Debe escojer un ID Valido y Asignado:\n'\
                'Por favor intente de nuevo'
        await update.message.reply_text(mensaje, reply_markup=markupOk)
        return ASI_CAMBIOESTATUS

    mensaje='Por favor, ingrese un comentario sobre el cambio de estatus:\n'
    
    await update.message.reply_text(mensaje, reply_markup=markupOk)
    return ASI_CAMBIOESTATUS

async def asi_comentar(update: Update, context: CallbackContext) -> int:

    mensaje='Por favor ingrese el comentario sobre el avance del ticket:'

    await update.message.reply_text(mensaje, reply_markup=markupCancelar)

    return ASI_COMENTAR

async def asi_db_comentar(update: Update, context: CallbackContext) -> int:
    
    SQL='INSERT INTO tickets_avances (ticket_id, departamento_id, asignado_a, descripcion, imagen, estatus_id) VALUES ('\
        f'{context.user_data[update.effective_chat.id]["ticket_id"]}, '\
        f'"{context.user_data[update.effective_chat.id]["departamento_id"]}", '\
        f'"{context.user_data[update.effective_chat.id]["asignado_a"]}", '\
        f'"{update.message.text}", '\
        f'"{context.user_data[update.effective_chat.id]["imagen"]}", '\
        f'{context.user_data[update.effective_chat.id]["status_id"]})'

    db.ejecutar_actualizacion(consulta=SQL)

    mensaje='El ticket se actulizó con éxito!!'

    await update.message.reply_text(mensaje, reply_markup=markupOk)

    return ConversationHandler.END

#-------------------------------------------------------
#-------------------------------------------------------
#-------------------------------------------------------
#                 Validacion de cierre
#-------------------------------------------------------
#-------------------------------------------------------
#-------------------------------------------------------

async def validar_cierre(update: Update, context: CallbackContext) -> int:
    
    SQL='SELECT tt.ticket_id as Ticket, tt.descripcion as Descripción, ce.nombre as Estatus, tt.departamento_id as departamento_id, tt.asignado_a '\
        'FROM (tele_tickets tt JOIN cat_estatus ce ON (tt.estatus_id = ce.estatus_id)) '\
        f'WHERE tt.estatus_id = 4  AND validado = 0 AND username = "{context.user_data[update.effective_chat.id]["username"][0]}"'
    

    df_t_asignados=db.ejecutar_consulta(consulta=SQL, columns=['Ticket', 'Descripción', 'Estatus', 'departamento_id', 'asignado_a'])
    df_t_asignados_lim = df_t_asignados[['Ticket', 'Descripción', 'Estatus']]

    context.user_data[update.effective_chat.id]['ticket_id']=int(df_t_asignados['Ticket'][0])
    context.user_data[update.effective_chat.id]['departamento_id']=int(df_t_asignados['departamento_id'][0])
    context.user_data[update.effective_chat.id]['asignado_a']=df_t_asignados['asignado_a'][0]

    if df_t_asignados.empty:
        mensaje='No tiene Tickets pendientes de validación.'
    else:
        mensaje='Esta es la lista de tickets pendientes de validación:\n\n'\
                f'{df_t_asignados_lim.to_string(index=False)}\n\n'\
                'Seleccione el ID del ticket con el que desea Trabajar.'
    
    await update.message.reply_text(mensaje, reply_markup=markupOk )

    return VALIDAR_CIERRE

async def val_val_reabrir(update: Update, context: CallbackContext) -> int:

    mensaje='Si valida el cierre presione el boton: Validado.\n\n'\
            'De lo contrario presione el boton: Re-Abrir.'

    await update.message.reply_text(mensaje, reply_markup=markupValidadoReAbrir) 

    return VAL_VAL_REABRIR

async def val_validado(update: Update, context: CallbackContext) -> int:

    SQL=f'UPDATE crm.tele_tickets SET validado = 1 WHERE (ticket_id = {context.user_data[update.effective_chat.id]["ticket_id"]}) and (departamento_id = {context.user_data[update.effective_chat.id]["departamento_id"]});'

    db.ejecutar_actualizacion(consulta=SQL)
    
    mensaje='El Ticket a sido validado.\n\n'\

    await update.message.reply_text(mensaje, reply_markup=markupOk) 

    return ConversationHandler.END

async def val_reabrir(update: Update, context: CallbackContext) -> int:

    mensaje='Por favor describa por que fue Re-Abierto el ticket:\n\n'

    await update.message.reply_text(mensaje) 

    return VAL_VAL_REABRIR

async def rea_foto(update: Update, context: CallbackContext) -> int:

    if update.message.text != 'Si': 
        context.user_data[update.effective_chat.id]['descripcion']=update.message.text
        mensaje='¿Requiere tomar una foto al objeto reportado?'
    elif update.message.text == 'Si':
            
        mensaje='Por favor, Tome la foto.'
    
    await update.message.reply_text(mensaje, reply_markup=markupSiNo)
    
    return REA_FOTO

async def rea_db(update: Update, context: CallbackContext) -> int:
    
    if update.message.text!='No':
        foto_file = await update.message.photo[-1].get_file()
        dir_archivo=f'{PATH_FOTO}{foto_file.file_unique_id}.jpg'
        await foto_file.download_to_drive(dir_archivo)
        context.user_data[update.effective_chat.id]['imagen']=f'{foto_file.file_unique_id}.jpg'
    else:
        context.user_data[update.effective_chat.id]['imagen']='Sin Foto'    
    #--------------- Fin Foto ---------------------------

    SQL_update=f'UPDATE tele_tickets SET estatus_id = 5 WHERE ticket_id={context.user_data[update.effective_chat.id]["ticket_id"]} AND departamento_id={context.user_data[update.effective_chat.id]["departamento_id"]}'
    SQL_insert='INSERT INTO tickets_avances (ticket_id, departamento_id, asignado_a, descripcion, imagen, estatus_id) VALUES ('\
                f'{context.user_data[update.effective_chat.id]["ticket_id"]}, '\
                f'"{context.user_data[update.effective_chat.id]["departamento_id"]}", '\
                f'"{context.user_data[update.effective_chat.id]["asignado_a"]}", '\
                f'"{context.user_data[update.effective_chat.id]["descripcion"]}", '\
                f'"{context.user_data[update.effective_chat.id]["imagen"]}", '\
                f'5)'

    db.ejecutar_actualizacion(consulta=SQL_update)
    db.ejecutar_actualizacion(consulta=SQL_insert)

    mensaje='El ticket fue re-abierto.'

    await update.message.reply_text(mensaje, reply_markup=markupOk)

    return ConversationHandler.END

#-------------------------------------------------------
#-------------------------------------------------------
#-------------------------------------------------------
#                 Programa Principal
#-------------------------------------------------------
#-------------------------------------------------------
#-------------------------------------------------------

def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()
    # Add conversation handler with the states CHOOSING, TY10PING_CHOICE and TYPING_REPLY
    conv_handler = ConversationHandler(
        #entry_points=[CommandHandler("start", start)],
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, start)],
        states={
            START: [
                MessageHandler(filters.Regex("^[0-9]+$"), ticket),
                MessageHandler(filters.Regex(r'^.*$'), start),
            ],
            VALIDAR_AHORA: [
                MessageHandler(filters.Regex("Si"), validar_cierre),
                MessageHandler(filters.Regex("No"), ticket),
                MessageHandler(filters.Regex(r'^.*$'), start),
            ],
            MENU_PRINCIPAL:[
                MessageHandler(filters.Regex("Nuevo"), departamentos),
                MessageHandler(filters.Regex("Abiertos"), t_abiertos),
                MessageHandler(filters.Regex("Asignados"), t_asignados),
                MessageHandler(filters.Regex("Validar"), validar_cierre),
                MessageHandler(filters.Regex(r'^.*$'), start),
            ],
            DEPARTAMENTOS:[
                MessageHandler(filters.Regex("^[0-9]+$"), ticket),
                MessageHandler(filters.Regex(r'^.*$'), departamentos),
            ], 
            TICKET:[
                MessageHandler(filters.Regex("^[0-9]+$"), ticket),
                MessageHandler(filters.Regex(r'^.*$'), foto),
            ],
            FOTO: [
                MessageHandler(filters.PHOTO, sla),
                MessageHandler(filters.Regex("^(Si)$"), foto),
                MessageHandler(filters.Regex("^(No)$"), slaSF),
                MessageHandler(filters.Regex(r'^.*$'), caracterInvalido),
            ],
            SLA: [
                MessageHandler(filters.Regex("^[0-9]+$"), despedida),
                MessageHandler(filters.Regex(r'^.*$'), caracterInvalido),
            ],
            #------------------ Tickets Abiertos --------------------------
            T_ABIERTOS: [
                MessageHandler(filters.Regex(r'^.*$'), t_a_detalle),
            ], 
            T_A_DETALLE: [
                MessageHandler(filters.Regex(r"^\d{1,4}$"), t_a_comentar),
            ], 
            T_A_COMENTAR: [
                MessageHandler(filters.Regex("Cambiar Estatus"),asi_cambioEstatus),
                MessageHandler(filters.Regex("Comentar"), asi_comentar),
                MessageHandler(filters.Regex(r'^.*$'), start),
            ],
            T_A_CAMBIOESTATUS: [
                MessageHandler(filters.Regex(r"^\d{1}$"), asi_bd_Estatus),
                MessageHandler(filters.Regex(r'^.*$'), t_asignados),
            ],                        
            #------------------ Tickets Asignados --------------------------
            T_ASIGNADOS: [
                MessageHandler(filters.Regex(r"^\d{1,3}$"), asi_asignado),
                MessageHandler(filters.Regex("Actualizar"), start),
                MessageHandler(filters.Regex(r'^.*$'), t_asignados),
            ],
            ASI_SELECCIONA: [
                MessageHandler(filters.Regex(r"^\d{1,3}$"), asi_cambioEstatus),
                MessageHandler(filters.Regex("Cambiar Estatus"),asi_cambioEstatus),
                MessageHandler(filters.Regex("Comentar"), asi_comentar),
                MessageHandler(filters.Regex(r'^.*$'), t_asignados),
            ],
            ASI_CAMBIOESTATUS: [
                MessageHandler(filters.Regex(r"^\d{1}$"), asi_bd_Estatus),
                MessageHandler(filters.Regex(r'^.*$'), t_asignados),
            ],
            ASI_COMENTAR: [
                MessageHandler(filters.Regex("Cancelar"), t_asignados),
                MessageHandler(filters.Regex(r'^.*$'), asi_db_comentar),
            ],
            ASI_DB_ESTATUS: [
                MessageHandler(filters.Regex(r'^.*$'), start),
            ],
            
            #------------------ Validar Cierrre ----------------------------
            VALIDAR_CIERRE: [
                MessageHandler(filters.Regex(r"^\d{1}$"), val_val_reabrir),
                MessageHandler(filters.Regex(r'^.*$'), start),
            ],
            VAL_VAL_REABRIR: [
                MessageHandler(filters.Regex("Validado"),val_validado),
                MessageHandler(filters.Regex("Re Abrir"), val_reabrir),
                MessageHandler(filters.Regex(r'^.*$'), rea_foto),
            ],
            REA_FOTO: [
                MessageHandler(filters.PHOTO, rea_db),
                MessageHandler(filters.Regex("^(Si)$"), rea_foto),
                MessageHandler(filters.Regex("^(No)$"), rea_db),
                MessageHandler(filters.Regex(r'^.*$'), caracterInvalido),
            ],            
        },
        fallbacks=[MessageHandler(filters.Regex("^Done$"), despedida)],
        #-------Configuracion de TIMEOUT de conversación cuando no haya respuesta.
        conversation_timeout=360
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C, 
    application.run_polling()

if __name__ == "__main__":
    main()