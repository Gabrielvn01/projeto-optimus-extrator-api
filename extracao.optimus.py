import os
import sys
import requests
import urllib3
import pandas as pd
import io
import json
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Desabilita avisos de segurança para HTTPS
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURAÇÕES ---
USUARIO_LOCAL = "gabriel.viana"

def determinar_diretorio_destino():
    # Caminho específico para o Servidor
    CAMINHO_SERVIDOR = r"Z:\0-API OPTIMUS\Dados"
    
    try:
        nome_do_usuario = os.getlogin().lower()
    except:
        nome_do_usuario = "servidor"

    # 1. Se estiver no seu PC (Desenvolvimento)
    if USUARIO_LOCAL in nome_do_usuario:
        caminho = os.path.join(os.path.expanduser("~"), "Desktop", "BANCO_OPTIMUS_INDIVIDUAL")
    else:
        # 2. Se estiver no Servidor, tenta o caminho da rede Z:
        if os.path.exists(os.path.split(CAMINHO_SERVIDOR)[0]) or os.path.exists(CAMINHO_SERVIDOR):
            caminho = CAMINHO_SERVIDOR
        else:
            # Fallback: Se o Z: não estiver mapeado, salva na pasta do .exe
            if getattr(sys, 'frozen', False):
                caminho = os.path.dirname(sys.executable)
            else:
                caminho = os.path.dirname(os.path.abspath(__file__))

    # Cria a pasta caso não exista
    if not os.path.exists(caminho):
        try:
            os.makedirs(caminho)
        except:
            pass
    return caminho

CONFIG = {
    "login": "SEU_USUARIO",
    "senha": "SUA_SENHA",
    "auth_url": "https://api.empresa.com.br/api/Login",

    "endpoints": {
        "CORRETIVAS": "https://app.optimusprime.com.br/grupotb/api/OsCorretiva/Get",
        "PREVENTIVAS": "https://app.optimusprime.com.br/grupotb/api/OsPreventiva/Get",
        "NAOCONFORMIDADES": "https://app.optimusprime.com.br/grupotb/api/OsPreventiva/NaoConformidades",
        "ESTOQUE": "https://app.optimusprime.com.br/grupotb/api/Estoque/Get",
        "ESTOQUE_MOV": "https://app.optimusprime.com.br/grupotb/api/Estoque/Movimentacoes/Get",
        "TECNICO": "https://app.optimusprime.com.br/grupotb/api/Tecnico/Get",
        "TECNICO_HISTORICO": "https://app.optimusprime.com.br/grupotb/api/Tecnico/historicoAtendimento/Get", 
        "SOLICITACAO": "https://app.optimusprime.com.br/grupotb/api/Solicitacao/Get",
        "EQUIPAMENTO": "https://app.optimusprime.com.br/grupotb/api/Equipamento/Get",
        "CHECKLIST": "https://app.optimusprime.com.br/grupotb/api/Checklist/Get",
        "CHECKLIST_PROGRAMADO": "https://app.optimusprime.com.br/grupotb/api/Checklist/ChecklistProgramado",
        "CHECKLIST_CUSTO_M2": "https://app.optimusprime.com.br/grupotb/api/Checklist/CustoM2",
        "CHECKLIST_NAOCONF": "https://app.optimusprime.com.br/grupotb/api/Checklist/NaoConformidades"
    },
}

def autenticar_api(auth_url, login, senha):
    print("Tentando autenticar...")
    try:
        resp = requests.post(auth_url, json={"Login": login, "Senha": senha}, verify=False, timeout=30)
        resp.raise_for_status()
        print("Autenticação OK!")
        return resp.json()
    except Exception as e:
        print(f"Erro Auth: {e}")
        return {}

def extrair_e_salvar_individual(nome, url, token, lojas):
    # REGRA DE DATA FUTURA PARA APIs ESPECÍFICAS
    if nome in ["PREVENTIVAS", "CHECKLIST_PROGRAMADO"]:
        data_fim_exec = CONFIG["data_hoje"] + relativedelta(months=12)
        print(f"\n--- Extraindo {nome} (DATA ESTENDIDA ATÉ: {data_fim_exec.strftime('%d/%m/%Y')}) ---")
    else:
        data_fim_exec = CONFIG["data_hoje"]
        print(f"\n--- Extraindo {nome} ---")

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    lista_dfs = []
    atual = CONFIG["data_inicio"]
    intervalos = []
    
    # Gera os blocos de 5 meses
    while atual < data_fim_exec:
        proximo = atual + relativedelta(months=5)
        if proximo > data_fim_exec: 
            proximo = data_fim_exec
        intervalos.append((atual.strftime("%Y-%m-%d"), proximo.strftime("%Y-%m-%d")))
        atual = proximo + timedelta(days=1)

    inicio_global = time.time()

    for idx, (dta_de, dta_ate) in enumerate(intervalos):
        if (time.time() - inicio_global) > CONFIG["tempo_limite_api_segundos"]:
            print(f"  [!] Tempo limite atingido para {nome}.")
            break

        if idx % 10 == 0 or idx == len(intervalos) - 1:
            print(f"  -> {nome} | Bloco {idx+1}/{len(intervalos)}: {dta_de} a {dta_ate}")

        body = {"tip_neg": lojas, "dtaDe": dta_de, "dtaAte": dta_ate}
        
        # Regra do TipChk="A" para Checklists (exceto Custo M2)
        if "CHECKLIST" in nome.upper() and "CUSTO_M2" not in nome.upper():
            body["TipChk"] = "A"

        try:
            s = requests.Session()
            req = requests.Request('GET', url, headers=headers, data=json.dumps(body))
            resp = s.send(req.prepare(), verify=False, timeout=120)
            
            if resp.status_code == 200 and resp.text.strip():
                df_temp = pd.read_json(io.StringIO(resp.text))
                if not df_temp.empty:
                    lista_dfs.append(df_temp)
        except:
            continue

    if lista_dfs:
        df_final = pd.concat(lista_dfs, ignore_index=True).drop_duplicates()
        caminho_arquivo = os.path.join(CONFIG["diretorio_destino"], f"{nome}.xlsx")
        
        df_final.to_excel(caminho_arquivo, index=False, engine='xlsxwriter')
        print(f"  [SUCESSO] Arquivo salvo em: {caminho_arquivo} ({len(df_final)} linhas)")
    else:
        print(f"  [AVISO] Nenhum dado para {nome}.")

if __name__ == "__main__":
    try:
        print(f"DIRETÓRIO DE DESTINO CONFIGURADO: {CONFIG['diretorio_destino']}")
        auth = autenticar_api(CONFIG["auth_url"], CONFIG["login"], CONFIG["senha"])
        token = auth.get("token")
        lojas = list(auth.get("tipoNegocios", {}).keys())
        
        if token and lojas:
            for nome, url in CONFIG["endpoints"].items():
                extrair_e_salvar_individual(nome, url, token, lojas)
            print(f"\n*** PROCESSO CONCLUÍDO COM SUCESSO! ***")
        else:
            print("Erro Crítico: Falha na autenticação.")
    except Exception as e:
        # Cria um log de erro caso o executável feche sozinho ou ocorra alguma exceção fatal
        with open("LOG_ERRO_EXECUTAVEL.txt", "a") as f:
            f.write(f"{datetime.now()}: Ocorreu um erro fatal: {str(e)}\n")
        raise e