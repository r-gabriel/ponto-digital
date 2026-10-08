import cv2
import os
import pandas as pd
from deepface import DeepFace
# Importa o módulo de mensagens do tkinter
import tkinter as tk
from tkinter import messagebox

# Inicializa o tkinter e oculta a janela principal (queremos apenas os pop-ups)
root = tk.Tk()
root.withdraw()

# Caminho para a pasta com as fotos dos funcionários cadastrados
DB_PATH = "banco_funcionarios"

# Inicializa a captura da webcam (0 é geralmente a câmera padrão)
cap = cv2.VideoCapture(0)

print("Sistema de Ponto Facial Iniciado. Pressione 'q' para sair ou 'p' para registrar o ponto.")

while True:
    ret, frame = cap.read()
    if not ret:
        messagebox.showerror("Erro de Hardware", "Não foi possível acessar a câmera de captura.")
        break

    # Exibe o feed de vídeo na tela para o funcionário se posicionar
    cv2.imshow("Registro de Ponto - Posicione seu rosto", frame)

    key = cv2.waitKey(1) & 0xFF

    # Se o usuário pressionar 'p', o sistema captura o frame atual e valida o ponto
    if key == ord('p'):
        try:
            # Busca o rosto do frame atual na pasta de funcionários cadastrados
            dfs = DeepFace.find(
                img_path=frame,
                db_path=DB_PATH,
                model_name="VGG-Face",
                detector_backend="retinaface",
                enforce_detection=True
            )

            # Se encontrar correspondências válidas
            if isinstance(dfs, list) and len(dfs) > 0 and not dfs[0].empty:
                # Pega o resultado com maior similaridade (menor distância métrica)
                best_match_path = dfs[0].iloc[0]['identity']

                # Extrai o nome do arquivo/ID do funcionário a partir do caminho do arquivo
                file_name = os.path.basename(best_match_path)
                funcionario_id = os.path.splitext(file_name)[0]

                # Pop-up de Sucesso
                messagebox.showinfo(
                    "Ponto Registrado",
                    f"Sucesso!\n\nFuncionário Identificado.\nID: {funcionario_id}"
                )

                # --- INTEGRAÇÃO COM SEU SISTEMA EXISTENTE ---
                # Chame sua função interna aqui para salvar no banco de dados:
                # salvar_ponto_no_banco(funcionario_id)
                # ---------------------------------------------

            else:
                # Pop-up de Não Reconhecido
                messagebox.showwarning(
                    "Acesso Negado",
                    "Rosto não reconhecido no banco de dados do sistema.\n\nTente novamente ou procure o RH."
                )

        except ValueError:
            # Disparado se o enforce_detection=True não encontrar nenhum rosto no frame
            messagebox.showwarning(
                "Aviso de Detecção",
                "Nenhum rosto foi detectado.\n\nPor favor, aproxime-se mais da câmera e fique parado."
            )
        except Exception as e:
            # Captura falhas inesperadas no processamento
            messagebox.showerror(
                "Erro no Sistema",
                f"Ocorreu uma falha interna no processamento:\n{str(e)}"
            )

    # Pressione 'q' para fechar a câmera e encerrar o loop
    elif key == ord('q'):
        break

# Libera os recursos da câmera e fecha janelas
cap.release()
cv2.destroyAllWindows()
root.destroy()