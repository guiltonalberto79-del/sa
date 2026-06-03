import flet as ft
import os
from datetime import datetime

# === CONTROLE DE ALERTAS DE PRAZO (7 DIAS) ===
def verificar_alerta(data_prazo_str):
    if not data_prazo_str:
        return False, ""
    try:
        # Converte a data do prazo (ex: "10/06/2026") para objeto data
        data_prazo = datetime.strptime(data_prazo_str, "%d/%m/%Y")
        hoje = datetime.now()
        
        # Reseta as horas para comparar apenas os dias
        data_prazo = data_prazo.replace(hour=0, minute=0, second=0, microsecond=0)
        hoje = hoje.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Calcula quantos dias faltam
        diferenca = data_prazo - hoje
        
        # Se faltam entre 0 e 7 dias, retorna True para o alerta
        if 0 <= diferenca.days <= 7:
            return True, f"Faltam {diferenca.days} dias!"
        return False, ""
    except:
        return False, "Data inválida"

# ==========================================
# AGENDA LUXO - TERMINAL STYLE (FLET APP)
# ==========================================

class TaskItem:
    def __init__(self, id_task, title, category, file_path=None, status="Pendente", sender="", received_date="", deadline="", is_repeated=False):
        self.id = id_task
        self.title = title
        self.category = category       # Um dos 5 círculos/classes dinâmicos
        self.file_path = file_path     # Ficheiro anexado em disco local
        self.status = status           # "Concluída", "Pendente", "Quase no fim", "Cancelada"
        self.sender = sender
        self.received_date = received_date
        self.deadline = deadline
        self.is_repeated = is_repeated

def main(page: ft.Page):
    # Configurações iniciais de janela desktop de Luxo
    page.title = "AETHER v2.0"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0A0A0A"
    page.padding = 0
    
    # Responsividade e tamanhos desktop ideais
    page.window.width = 1000
    page.window.height = 740
    page.window.min_width = 850
    page.window.min_height = 600

    # Cores da Paleta de Luxo Terminal
    COLOR_BG = "#0A0A0A"
    COLOR_PANEL = "#111111"
    COLOR_TEXT_PRIMARY = "#E5E9F0"
    COLOR_TEXT_MUTED = "#6B7280"
    
    # Mapeamento estrito do Dashboard de Alertas
    COLOR_CONCLUIDA = "#00FF66"   # Verde Neon
    COLOR_PENDENTE = "#FFCC00"    # Amarelo
    COLOR_QUASE_FIM = "#FF4500"   # Laranja/Vermelho
    COLOR_CANCELADA = "#4B5563"   # Cinza

    # Mapeamento padrão de cores das 5 Categorias/Classes
    CATEGORIES_CFG = {
        "cat1": {"color": "#00FF66", "bg": "rgba(0, 255, 102, 0.1)"},
        "cat2": {"color": "#00E5FF", "bg": "rgba(0, 229, 255, 0.1)"},
        "cat3": {"color": "#BD00FF", "bg": "rgba(189, 0, 255, 0.1)"},
        "cat4": {"color": "#FF9900", "bg": "rgba(255, 153, 0, 0.1)"},
        "cat5": {"color": "#FF0055", "bg": "rgba(255, 0, 85, 0.1)"}
    }

    # Nomes iniciais customizáveis das 5 classes (comportamento dinâmico solicitado pela engrenagem)
    classes_names = {
        "cat1": "Core",
        "cat2": "Ops",
        "cat3": "Sec",
        "cat4": "Sys",
        "cat5": "Net"
    }

    # Custom dynamic category photos
    classes_photos = {
        "cat1": "https://images.unsplash.com/photo-1579546929518-9e396f3cc809",
        "cat2": "https://images.unsplash.com/photo-1579546929622-6a2ca21af02a",
        "cat3": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe",
        "cat4": "https://images.unsplash.com/photo-1614850523459-c2f4c699c52e",
        "cat5": "https://images.unsplash.com/photo-1557683316-973673baf926"
    }

    # Banco de dados simulado inicial mapeado pelas chaves persistentes cat1 a cat5
    tasks_db = [
        TaskItem(1, "Otimizar Banco de Dados Oracle", "cat1", "db_backup.sql", "Pendente", "Gerência Core", "01/06/2026", "10/06/2026", False),
        TaskItem(2, "Revisar logs de intrusão na AWS", "cat3", "firewall_report.pdf", "Quase no fim", "Ops AWS Sec", "02/06/2026", "04/06/2026", True),
        TaskItem(3, "Agendar reunião com stakeholders", "cat2", None, "Concluída", "Diretoria", "03/06/2026", "03/06/2026", False),
        TaskItem(4, "Migração de DNS das rotas", "cat5", "named.conf", "Pendente", "Infra Adm", "02/06/2026", "05/06/2026", False),
        TaskItem(5, "Atualizar dependências NPM", "cat4", None, "Cancelada", "Npm Bot", "01/06/2026", "03/06/2026", True),
        TaskItem(6, "Implementar firewall de aplicação", "cat3", None, "Pendente", "AWS Cloud", "03/06/2026", "15/06/2026", False),
    ]

    current_category_filter = None  # Filtro focado (chave cat1-cat5 ou None)
    uploaded_file_temp = None       # Buffer temporário para anexo de arquivo

    # Referências para Atualização Dinâmica na GUI
    tasks_container = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    status_summary_row = ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, expand=True)
    active_filter_label = ft.Text("Filtro: Todas as categorias", color=COLOR_TEXT_MUTED, size=12, italic=True)
    footer = ft.Container(
        content=ft.Row([
            ft.Text("Agenda Pessoal", size=12, color=COLOR_TEXT_MUTED, weight=ft.FontWeight.BOLD)
        ], alignment=ft.MainAxisAlignment.CENTER),
        padding=10
    )

    # === GESTÃO DE ARQUIVOS (FILE PICKER) ===
    def on_file_picker_result(e: ft.FilePickerResultEvent):
        nonlocal uploaded_file_temp
        if e.files:
            uploaded_file_temp = e.files[0].path
            temp_file_label.value = f"📎 Selecionado: {e.files[0].name} ({round(e.files[0].size/1024, 1)} KB)"
            temp_file_label.color = COLOR_CONCLUIDA
            temp_file_label.visible = True
            page.show_snack_bar(ft.SnackBar(ft.Text(f"Arquivo anexado com sucesso: {e.files[0].name}", color=COLOR_CONCLUIDA), bgcolor=COLOR_PANEL))
        else:
            uploaded_file_temp = None
            temp_file_label.visible = False
        page.update()

    file_picker = ft.FilePicker(on_result=on_file_picker_result)
    page.overlay.append(file_picker)

    # === GESTÃO DE FOTOS DE CLASSE (FILE PICKER) ===
    classe_atual_upload = [None]
    temp_photos = {
        "cat1": "",
        "cat2": "",
        "cat3": "",
        "cat4": "",
        "cat5": ""
    }

    avatar1 = ft.CircleAvatar(foreground_image_url="", radius=16)
    avatar2 = ft.CircleAvatar(foreground_image_url="", radius=16)
    avatar3 = ft.CircleAvatar(foreground_image_url="", radius=16)
    avatar4 = ft.CircleAvatar(foreground_image_url="", radius=16)
    avatar5 = ft.CircleAvatar(foreground_image_url="", radius=16)

    def ao_selecionar_imagem(e: ft.FilePickerResultEvent):
        if e.files and classe_atual_upload[0]:
            caminho_da_foto = e.files[0].path
            classe = classe_atual_upload[0]
            temp_photos[classe] = caminho_da_foto
            
            # Atualiza dinamicamente o avatar correspondente na janela
            if classe == "cat1": avatar1.foreground_image_url = caminho_da_foto
            elif classe == "cat2": avatar2.foreground_image_url = caminho_da_foto
            elif classe == "cat3": avatar3.foreground_image_url = caminho_da_foto
            elif classe == "cat4": avatar4.foreground_image_url = caminho_da_foto
            elif classe == "cat5": avatar5.foreground_image_url = caminho_da_foto
            
            page.update()

    seletor_fotos = ft.FilePicker(on_result=ao_selecionar_imagem)
    page.overlay.append(seletor_fotos)

    # === GESTAO DE ATUALIZACAO DE ANEXO EM TAREFAS EXISTENTES ===
    task_upload_id = [None]
    
    def ao_atualizar_anexo(e: ft.FilePickerResultEvent):
        if e.files and task_upload_id[0] is not None:
            caminho_da_foto = e.files[0].path
            nome_arquivo = e.files[0].name
            tamanho = round(e.files[0].size / 1024, 1)
            str_tamanho = f"{tamanho} MB" if tamanho > 1024 else f"{tamanho} KB"
            # Update DB
            for t in tasks_db:
                if t.id == task_upload_id[0]:
                    t.file_name = nome_arquivo
                    t.file_size = str_tamanho
                    break
            
            page.show_snack_bar(ft.SnackBar(ft.Text(f"Documento atualizado para {nome_arquivo}"), bgcolor=COLOR_CONCLUIDA))
            update_tasks_view()
            if hasattr(page, 'dialog') and page.dialog and page.dialog.open:
                # Atualizar visualmente no dialog
                page.dialog.open = False
                page.update()
                
    seletor_update_file = ft.FilePicker(on_result=ao_atualizar_anexo)
    page.overlay.append(seletor_update_file)

    def get_status_color(status):
        if status == "Concluída":
            return COLOR_CONCLUIDA
        elif status == "Pendente":
            return COLOR_PENDENTE
        elif status == "Quase no fim":
            return COLOR_QUASE_FIM
        # === GESTÃO DE DETALHES DE ATIVIDADES (MODAL CLICK DIALOG) ===
    def view_task_details(e, task):
        page = e.page
        
        # Obter propriedades de forma robusta para suportar dicionário ou objeto
        title = task.title if hasattr(task, 'title') else task.get('title', '')
        sender = task.sender if hasattr(task, 'sender') else task.get('sender', '')
        received = task.received_date if hasattr(task, 'received_date') else (task.get('received_date') or task.get('received', ''))
        deadline = task.deadline if hasattr(task, 'deadline') else task.get('deadline', '')
        file_path = task.file_path if hasattr(task, 'file_path') else (task.get('file_path') or task.get('fileName', ''))
        file_name = os.path.basename(file_path) if file_path else (task.get('file_name') or task.get('fileName', 'Nenhum'))
        file_size = task.file_size if hasattr(task, 'file_size') else task.get('file_size', '0 KB')
        task_id = task.id if hasattr(task, 'id') else task.get('id', 0)
        
        category_key = task.category if hasattr(task, 'category') else task.get('category', 'cat1')
        status = task.status if hasattr(task, 'status') else task.get('status', 'Pendente')
        is_repeated_flag = task.is_repeated if hasattr(task, 'is_repeated') else task.get('is_repeated', False)
        category_name = classes_names.get(category_key, "Desconhecido")
        
        is_alert, alert_msg = verificar_alerta(deadline)
        alert_text = alert_msg if (is_alert and status != "Concluída") else "Nenhum alerta ativo"

        # Função simulada de exportação do anexo
        def export_file(e):
            # Aqui você implementaria a lógica real de download
            page.show_snack_bar(ft.SnackBar(content=ft.Text(f"Exportando: {file_name}...")))

        def atualizar_anexo(e):
            task_upload_id[0] = task_id
            seletor_update_file.pick_files()

        # Componente reativo para exibir o status do anexo
        anexo_texto = ft.Text(f"{file_name} ({file_size})" if file_name and file_name != "Nenhum" else "Nenhum anexo", color="#00E5FF" if file_name and file_name != "Nenhum" else COLOR_TEXT_MUTED, italic=True, size=12)
        anexo_container = ft.Row([
            anexo_texto,
            ft.IconButton(ft.icons.DOWNLOAD, on_click=export_file, icon_color="#00E5FF", icon_size=16) if file_name and file_name != "Nenhum" else ft.Container(width=0, height=0),
            ft.ElevatedButton("Atualizar" if file_name and file_name != "Nenhum" else "Anexar", on_click=atualizar_anexo, bgcolor="#1A1A1A", color="#00E5FF", height=24)
        ], spacing=5)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Container(
                    content=ft.Text(category_name.upper(), size=10, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY),
                    border=ft.border.all(1, CATEGORIES_CFG.get(category_key, {}).get("color", COLOR_TEXT_MUTED)),
                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                    border_radius=3
                ),
                ft.Text(status.upper(), size=12, weight=ft.FontWeight.BOLD, color=get_status_color(status))
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            content=ft.Container(
                width=450,
                padding=10,
                content=ft.Column([
                    ft.Text(f"Detalhes: {title}", size=15, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY),
                    ft.Divider(color="#222222"),
                    ft.Row([
                        ft.Text("Remetente:", color=COLOR_TEXT_MUTED, size=12),
                        ft.Text(sender if sender else "Não especificado", color=COLOR_TEXT_PRIMARY, size=12, weight=ft.FontWeight.SEMI_BOLD)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([
                        ft.Text("Recebido:", color=COLOR_TEXT_MUTED, size=12),
                        ft.Text(received if received else "Não especificado", color=COLOR_TEXT_PRIMARY, size=12)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([
                        ft.Text("Prazo:", color=COLOR_TEXT_MUTED, size=12),
                        ft.Text(deadline if deadline else "Não especificado", color=COLOR_PENDENTE, size=12, weight=ft.FontWeight.BOLD)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([
                        ft.Text("Anexo / Ficheiro:", color=COLOR_TEXT_MUTED, size=12),
                        anexo_container
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([
                        ft.Text("Alerta de Prazo:", color=COLOR_TEXT_MUTED, size=12),
                        ft.Text(f"⏰ {alert_text}" if is_alert and status != "Concluída" else alert_text, color=COLOR_QUASE_FIM if is_alert and status != "Concluída" else COLOR_TEXT_MUTED, size=12)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([
                        ft.Text("Atividade Repetida:", color=COLOR_TEXT_MUTED, size=12),
                        ft.Text("Sim ⚠️" if is_repeated_flag else "Não", color=COLOR_PENDENTE if is_repeated_flag else COLOR_TEXT_MUTED, size=12)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                ], tight=True, spacing=12),
            ),
            actions=[
                ft.ElevatedButton("Fechar", on_click=lambda e: setattr(dlg, 'open', False) or page.update(), bgcolor="blue", color="white")
            ],
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

    # === ATUALIZAÇÃO DA WORKSPACE (RENDER DAS TAREFAS) ===
    def update_tasks_view():
        tasks_container.controls.clear()
        
        # Filtrar as tarefas conforme a seleção do círculo ativo
        filtered_list = tasks_db
        if current_category_filter:
            filtered_list = [t for t in tasks_db if t.category == current_category_filter]
            cat_alias = classes_names[current_category_filter]
            active_filter_label.value = f"Filtro Ativo: [{cat_alias.upper()}]"
            active_filter_label.color = CATEGORIES_CFG[current_category_filter]["color"]
        else:
            active_filter_label.value = "Filtro: Todas as categorias"
            active_filter_label.color = COLOR_TEXT_MUTED

        # Ordenar tarefas por status e prazo (pouco tempo restante primeiro, concluidas/canceladas no fim)
        def get_sort_key(t):
            is_alert = False
            days_left = 999999
            if t.deadline:
                try:
                    data_prazo = datetime.strptime(t.deadline, "%d/%m/%Y")
                    hoje = datetime.now()
                    data_prazo = data_prazo.replace(hour=0, minute=0, second=0, microsecond=0)
                    hoje = hoje.replace(hour=0, minute=0, second=0, microsecond=0)
                    diferenca = data_prazo - hoje
                    days_left = diferenca.days
                    if days_left <= 7 and t.status != "Concluída":
                        is_alert = True
                except:
                    pass

            if is_alert:
                status_priority = 0
            elif t.status not in ["Concluída", "Cancelada"]:
                status_priority = 1
            elif t.status == "Concluída":
                status_priority = 2
            elif t.status == "Cancelada":
                status_priority = 3
            else:
                status_priority = 4

            return (status_priority, days_left)

        filtered_list = sorted(filtered_list, key=get_sort_key)

        if not filtered_list:
            tasks_container.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.icons.LAYERS_CLEAR_OUTLINED, size=40, color=COLOR_TEXT_MUTED),
                        ft.Text("Nenhuma tarefa ativa neste filtro.", color=COLOR_TEXT_MUTED, size=13, font_family="monospace")
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                    padding=40,
                )
            )
        else:
            for task in filtered_list:
                cat_color = CATEGORIES_CFG[task.category]["color"]
                cat_alias = classes_names[task.category]
                status_color = get_status_color(task.status)

                # Controle de Alerta pela função de verificação sugerida
                is_alert, alert_msg = verificar_alerta(task.deadline)
                is_active_alert = is_alert and task.status != "Concluída"

                card_border_color = "#222222"
                if task.status == "Concluída":
                    card_border_color = "#142D1C"
                elif is_active_alert:
                    card_border_color = COLOR_QUASE_FIM

                # Card de Tarefa de luxo otimizado conforme especificações
                task_card = ft.Container(
                    bgcolor=COLOR_PANEL,
                    border=ft.border.all(1, card_border_color),
                    border_radius=10,
                    padding=16,
                    margin=ft.margin.only(bottom=2),
                    content=ft.Row([
                        # Status indicator (borda esquerda verde/amarelo/laranja/cinza)
                        ft.Row([
                            ft.Container(
                                width=6,
                                height=38,
                                bgcolor=status_color,
                                border_radius=3,
                            ),
                            # Título da tarefa, classe e anexo em colunas limpas (Clicável para ver Detalhes)
                            ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Text(task.title, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY, size=14,
                                                style=ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH if task.status == "Concluída" else None)),
                                        ft.Container(
                                            content=ft.Text(cat_alias.upper(), size=10, color=cat_color, weight=ft.FontWeight.BOLD),
                                            border=ft.border.all(1, cat_color),
                                            border_radius=4,
                                            padding=ft.padding.symmetric(horizontal=6, vertical=2)
                                        )
                                    ], spacing=10),
                                    ft.Row([
                                        ft.Text(f"Status: {task.status}", size=11, color=status_color),
                                        ft.Text(" • " if task.file_path else "", size=11, color=COLOR_TEXT_MUTED),
                                        ft.Text(f"📎 {os.path.basename(task.file_path)}" if task.file_path else "", size=11, color=COLOR_TEXT_MUTED, italic=True)
                                    ], spacing=4),
                                    ft.Row([
                                        ft.Text(f"De: {task.sender}" if task.sender else "De: N/A", size=11, color=COLOR_TEXT_MUTED),
                                        ft.Text(" | " if task.received_date else "", size=11, color=COLOR_TEXT_MUTED),
                                        ft.Text(f"Recebido: {task.received_date}" if task.received_date else "", size=11, color=COLOR_TEXT_MUTED),
                                        ft.Text(" | " if task.deadline else "", size=11, color=COLOR_TEXT_MUTED),
                                        ft.Text(f"Prazo: {task.deadline}" if task.deadline else "", size=11, color=COLOR_TEXT_MUTED),
                                        ft.Text(" | " if is_active_alert else "", size=11, color=COLOR_TEXT_MUTED),
                                        ft.Text(f"⏰ {alert_msg}" if is_active_alert else "", size=11, color=COLOR_QUASE_FIM, weight=ft.FontWeight.BOLD),
                                        ft.Text(" | " if task.is_repeated else "", size=11, color=COLOR_TEXT_MUTED),
                                        ft.Text("⚠️ Alerta: Repetida" if task.is_repeated else "", size=11, color=COLOR_PENDENTE, weight=ft.FontWeight.BOLD)
                                    ], spacing=4)
                                ], spacing=4),
                                on_click=lambda e, t=task: view_task_details(e, t),
                                expand=True
                            )
                        ], spacing=12, expand=True),

                        # Ações à direita (Dropdown + Quick Actions)
                        ft.Row([
                            # Dropdown interativo de status
                            ft.Dropdown(
                                value=task.status,
                                options=[
                                    ft.dropdown.Option("Concluída"),
                                    ft.dropdown.Option("Pendente"),
                                    ft.dropdown.Option("Quase no fim"),
                                    ft.dropdown.Option("Cancelada")
                                ],
                                width=140,
                                height=36,
                                text_size=12,
                                border_color="#333333",
                                focused_border_color=COLOR_PENDENTE,
                                on_change=lambda e, t=task: change_task_status(t, e.control.value)
                            ),
                            # Botão Concluir/Reabrir rápido
                            ft.IconButton(
                                icon=ft.icons.CHECK_CIRCLE_OUTLINED if task.status != "Concluída" else ft.icons.REPLAY_CIRCLE_FILLED_OUTLINED,
                                icon_color=COLOR_CONCLUIDA if task.status != "Concluída" else COLOR_TEXT_MUTED,
                                tooltip="Concluir / Reiniciar tarefa",
                                on_click=lambda e, t=task: toggle_task_status(t)
                            ),
                            # Excluir
                            ft.IconButton(
                                icon=ft.icons.DELETE_OUTLINE,
                                icon_color="red",
                                tooltip="Excluir Atividade",
                                on_click=lambda e, t=task: delete_task(t)
                            )
                        ], spacing=8)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                )
                tasks_container.controls.append(task_card)

        # Atualizar a Barra de Status Inferior (Dashboard de Alertas)
        update_dashboard_stats()
        page.update()

    def change_task_status(task, new_status):
        task.status = new_status
        update_tasks_view()

    def toggle_task_status(task):
        task.status = "Concluída" if task.status != "Concluída" else "Pendente"
        update_tasks_view()

    def delete_task(task):
        tasks_db.remove(task)
        page.show_snack_bar(ft.SnackBar(ft.Text(f"✓ Tarefa removida: '{task.title}'")))
        circles_row.controls = build_kpi_circles() # Atualizar contadores
        update_tasks_view()

    # === ATUALIZAÇÃO DA BARRA DE STATUS INFERIOR (Dashboard de Alertas) ===
    def update_dashboard_stats():
        count_done = len([t for t in tasks_db if t.status == "Concluída"])
        count_pend = len([t for t in tasks_db if t.status == "Pendente"])
        count_due = len([t for t in tasks_db if t.status == "Quase no fim"])
        count_canc = len([t for t in tasks_db if t.status == "Cancelada"])

        status_summary_row.controls.clear()

        # Alinhamento à esquerda: Indicadores visuais de cores solicitado
        status_summary_row.controls.append(
            ft.Row([
                ft.Row([
                    ft.Container(width=8, height=8, bgcolor=COLOR_CONCLUIDA, border_radius=4),
                    ft.Text(f"Concluídas: {count_done}", color=COLOR_CONCLUIDA, size=11, weight=ft.FontWeight.BOLD)
                ], spacing=6),
                ft.Row([
                    ft.Container(width=8, height=8, bgcolor=COLOR_PENDENTE, border_radius=4),
                    ft.Text(f"Pendentes: {count_pend}", color=COLOR_PENDENTE, size=11, weight=ft.FontWeight.BOLD)
                ], spacing=6),
                ft.Row([
                    ft.Container(width=8, height=8, bgcolor=COLOR_QUASE_FIM, border_radius=4),
                    ft.Text(f"Quase no fim: {count_due}", color=COLOR_QUASE_FIM, size=11, weight=ft.FontWeight.BOLD)
                ], spacing=6),
                ft.Row([
                    ft.Container(width=8, height=8, bgcolor=COLOR_CANCELADA, border_radius=4),
                    ft.Text(f"Canceladas: {count_canc}", color=COLOR_CANCELADA, size=11, weight=ft.FontWeight.BOLD)
                ], spacing=6)
            ], spacing=16)
        )

        # Mensagem de Alerta de criticidade (Lado Direito)
        alert_msg = "SISTEMA SEGURO: Estabilidade Operacional"
        alert_color = COLOR_CONCLUIDA
        if count_due > 0:
            alert_msg = f"CRITICAL SYSTEM DELAY: {count_due} ATIVIDADES LIMITES!"
            alert_color = COLOR_QUASE_FIM
        elif count_pend > 3:
            alert_msg = "ALERTA DE SOBREGARGA: Alta taxa de pendências"
            alert_color = COLOR_PENDENTE

        status_summary_row.controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.REPORT_PROBLEM_OUTLINED, size=14, color=alert_color),
                    ft.Text(alert_msg, color=alert_color, size=11, weight=ft.FontWeight.BOLD, font_family="monospace")
                ], spacing=5),
                border=ft.border.all(1, alert_color),
                border_radius=4,
                padding=ft.padding.symmetric(horizontal=8, vertical=3)
            )
        )

    # === CONFIGURAÇÃO DAS CLASSES (ENGRENAGEM CLICK DIALOG) ===
    def open_settings(e):
        # Inicializa as fotos atuais no temp_photos
        temp_photos["cat1"] = classes_photos["cat1"]
        temp_photos["cat2"] = classes_photos["cat2"]
        temp_photos["cat3"] = classes_photos["cat3"]
        temp_photos["cat4"] = classes_photos["cat4"]
        temp_photos["cat5"] = classes_photos["cat5"]

        avatar1.foreground_image_url = temp_photos["cat1"]
        avatar2.foreground_image_url = temp_photos["cat2"]
        avatar3.foreground_image_url = temp_photos["cat3"]
        avatar4.foreground_image_url = temp_photos["cat4"]
        avatar5.foreground_image_url = temp_photos["cat5"]

        def disparar_upload(nome_classe):
            classe_atual_upload[0] = nome_classe
            seletor_fotos.pick_files(file_type=ft.FilePickerFileType.IMAGE)

        tf_cat1 = ft.TextField(value=classes_names["cat1"], dense=True, expand=True, bgcolor="#1A1A1A", border_color="#333333", focused_border_color=COLOR_PENDENTE)
        tf_cat2 = ft.TextField(value=classes_names["cat2"], dense=True, expand=True, bgcolor="#1A1A1A", border_color="#333333", focused_border_color=COLOR_PENDENTE)
        tf_cat3 = ft.TextField(value=classes_names["cat3"], dense=True, expand=True, bgcolor="#1A1A1A", border_color="#333333", focused_border_color=COLOR_PENDENTE)
        tf_cat4 = ft.TextField(value=classes_names["cat4"], dense=True, expand=True, bgcolor="#1A1A1A", border_color="#333333", focused_border_color=COLOR_PENDENTE)
        tf_cat5 = ft.TextField(value=classes_names["cat5"], dense=True, expand=True, bgcolor="#1A1A1A", border_color="#333333", focused_border_color=COLOR_PENDENTE)

        def save_settings(e):
            if not all([tf_cat1.value, tf_cat2.value, tf_cat3.value, tf_cat4.value, tf_cat5.value]):
                page.show_snack_bar(ft.SnackBar(ft.Text("Nenhum nome de classe pode ficar em branco!", color="red"), bgcolor=COLOR_PANEL))
                return
            classes_names["cat1"] = tf_cat1.value.strip()
            classes_names["cat2"] = tf_cat2.value.strip()
            classes_names["cat3"] = tf_cat3.value.strip()
            classes_names["cat4"] = tf_cat4.value.strip()
            classes_names["cat5"] = tf_cat5.value.strip()

            classes_photos["cat1"] = temp_photos["cat1"]
            classes_photos["cat2"] = temp_photos["cat2"]
            classes_photos["cat3"] = temp_photos["cat3"]
            classes_photos["cat4"] = temp_photos["cat4"]
            classes_photos["cat5"] = temp_photos["cat5"]
            
            dropdown_new_cat.options = [ft.dropdown.Option(key, text=val) for key, val in classes_names.items()]

            settings_dialog.open = False
            circles_row.controls = build_kpi_circles() # Recarrega círculos com novos apelidos e fotos
            update_tasks_view()
            page.show_snack_bar(ft.SnackBar(ft.Text("✓ Configuração de classes atualizada com sucesso!", color=COLOR_CONCLUIDA), bgcolor="#142118"))

        settings_dialog = ft.AlertDialog(
            modal=True,
            bgcolor="#111111",
            shape=ft.RoundedRectangleBorder(radius=10),
            title=ft.Row([
                ft.Icon(ft.icons.SETTINGS, color="purple"),
                ft.Text("CONFIGURAR CLASSES", size=16, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY)
            ]),
            content=ft.Container(
                width=450,
                content=ft.Column([
                    ft.Text("Renomeie e adicione fotos às 5 categorias de círculos no simulador.", size=12, color="grey"),
                    ft.Divider(height=10, color="transparent"),
                    
                    # CLASSE 1 (Verde)
                    ft.Text("● CAT1 (Classe 1 (Verde)):", color="green", size=12, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        avatar1,
                        tf_cat1,
                        ft.IconButton(ft.icons.ADD_A_PHOTO, icon_color="green", on_click=lambda _: disparar_upload("cat1"), tooltip="Adicionar Foto")
                    ]),
                    
                    # CLASSE 2 (Azul)
                    ft.Text("● CAT2 (Classe 2 (Azul)):", color="cyan", size=12, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        avatar2,
                        tf_cat2,
                        ft.IconButton(ft.icons.ADD_A_PHOTO, icon_color="cyan", on_click=lambda _: disparar_upload("cat2"), tooltip="Adicionar Foto")
                    ]),

                    # CLASSE 3 (Roxo)
                    ft.Text("● CAT3 (Classe 3 (Roxo)):", color="purple", size=12, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        avatar3,
                        tf_cat3,
                        ft.IconButton(ft.icons.ADD_A_PHOTO, icon_color="purple", on_click=lambda _: disparar_upload("cat3"), tooltip="Adicionar Foto")
                    ]),

                    # CLASSE 4 (Laranja)
                    ft.Text("● CAT4 (Classe 4 (Laranja)):", color="orange", size=12, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        avatar4,
                        tf_cat4,
                        ft.IconButton(ft.icons.ADD_A_PHOTO, icon_color="orange", on_click=lambda _: disparar_upload("cat4"), tooltip="Adicionar Foto")
                    ]),

                    # CLASSE 5 (Vermelho)
                    ft.Text("● CAT5 (Classe 5 (Vermelho)):", color="red", size=12, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        avatar5,
                        tf_cat5,
                        ft.IconButton(ft.icons.ADD_A_PHOTO, icon_color="red", on_click=lambda _: disparar_upload("cat5"), tooltip="Adicionar Foto")
                    ]),
                ], tight=True, spacing=10)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: close_settings_dialog(settings_dialog)),
                ft.ElevatedButton("Salvar", bgcolor="green", color="white", on_click=save_settings)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        page.dialog = settings_dialog
        settings_dialog.open = True
        page.update()

    def close_settings_dialog(dlg):
        dlg.open = False
        page.update()

    # === DIALOG DE ADIÇÃO (POPUP COM TÍTULO, CATEGORIA, ANEXO E SALVAMENTO) ===
    txt_new_title = ft.TextField(
        label="Nome da Atividade",
        hint_text="ex: Revisar rotas de rede do switch Cisco",
        border_color="#333333",
        focused_border_color=COLOR_PENDENTE,
        color=COLOR_TEXT_PRIMARY,
        text_size=13,
        expand=True
    )
    txt_new_sender = ft.TextField(
        label="Quem enviou",
        hint_text="ex: Gerência de T.I.",
        border_color="#333333",
        focused_border_color=COLOR_PENDENTE,
        color=COLOR_TEXT_PRIMARY,
        text_size=13,
        expand=True
    )
    txt_new_received = ft.TextField(
        label="Data de Recebimento (DD/MM/AAAA)",
        hint_text="ex: 03/06/2026",
        border_color="#333333",
        focused_border_color=COLOR_PENDENTE,
        color=COLOR_TEXT_PRIMARY,
        text_size=13,
        expand=True
    )
    txt_new_deadline = ft.TextField(
        label="Prazo Final (DD/MM/AAAA)",
        hint_text="ex: 15/06/2026",
        border_color="#333333",
        focused_border_color=COLOR_PENDENTE,
        color=COLOR_TEXT_PRIMARY,
        text_size=13,
        expand=True
    )
    chk_new_repeated = ft.Checkbox(
        label="Atividade Repetida (Ativar alerta)",
        value=False
    )
    
    dropdown_new_cat = ft.Dropdown(
        label="Classe (Categoria)",
        options=[ft.dropdown.Option(key, text=val) for key, val in classes_names.items()],
        border_color="#333333",
        focused_border_color=COLOR_PENDENTE,
        color=COLOR_TEXT_PRIMARY,
        width=170
    )
    temp_file_label = ft.Text(visible=False, size=11, italic=True)

    def handle_add_task(e):
        nonlocal uploaded_file_temp
        if not txt_new_title.value:
            page.show_snack_bar(ft.SnackBar(ft.Text("O campo de título é obrigatório!", color="red"), bgcolor=COLOR_PANEL))
            return
        if not dropdown_new_cat.value:
            page.show_snack_bar(ft.SnackBar(ft.Text("Selecione uma das 5 categorias disponíveis!", color="red"), bgcolor=COLOR_PANEL))
            return

        new_id = max([t.id for t in tasks_db]) + 1 if tasks_db else 1
        new_task = TaskItem(
            id_task=new_id,
            title=txt_new_title.value,
            category=dropdown_new_cat.value, # Chave persistente (ex: cat1)
            file_path=uploaded_file_temp,
            status="Pendente",
            sender=txt_new_sender.value.strip() if txt_new_sender.value else "",
            received_date=txt_new_received.value.strip() if txt_new_received.value else "",
            deadline=txt_new_deadline.value.strip() if txt_new_deadline.value else "",
            is_repeated=chk_new_repeated.value if chk_new_repeated.value is not None else False
        )
        tasks_db.append(new_task)

        # Limpar buffers
        txt_new_title.value = ""
        txt_new_sender.value = ""
        txt_new_received.value = ""
        txt_new_deadline.value = ""
        chk_new_repeated.value = False
        dropdown_new_cat.value = None
        uploaded_file_temp = None
        temp_file_label.visible = False

        page.dialog.open = False
        circles_row.controls = build_kpi_circles() # Recarrega círculos
        update_tasks_view()
        page.show_snack_bar(ft.SnackBar(ft.Text("✓ Atividade registrada com sucesso!", color=COLOR_CONCLUIDA), bgcolor="#1F2F23"))

    def open_add_task_dialog(e):
        nonlocal uploaded_file_temp
        uploaded_file_temp = None
        txt_new_title.value = ""
        txt_new_sender.value = ""
        txt_new_received.value = ""
        txt_new_deadline.value = ""
        chk_new_repeated.value = False
        dropdown_new_cat.value = None
        temp_file_label.visible = False

        add_dialog = ft.AlertDialog(
            bgcolor="#111111",
            shape=ft.RoundedRectangleBorder(radius=10),
            content=ft.Container(
                width=500,
                padding=10,
                content=ft.Column([
                    ft.Text("REGISTAR NOVA TAREFA DE SISTEMA", size=14, weight=ft.FontWeight.BOLD, color=COLOR_PENDENTE, letter_spacing=1),
                    ft.Divider(color="#222222"),
                    txt_new_title,
                    txt_new_sender,
                    ft.Row([
                        txt_new_received,
                        txt_new_deadline
                    ], spacing=10),
                    chk_new_repeated,
                    ft.Row([
                        dropdown_new_cat,
                        ft.ElevatedButton(
                            "Anexar Arquivo",
                            icon=ft.icons.FILE_UPLOAD_OUTLINED,
                            color="#00E5FF",
                            bgcolor="#1F2C3F",
                            on_click=lambda _: file_picker.pick_files(allow_multiple=False)
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=10),
                    temp_file_label,
                    ft.Divider(color="#222222"),
                    ft.Row([
                        ft.TextButton("Cancelar", on_click=lambda _: close_add_dialog(add_dialog)),
                        ft.ElevatedButton("Salvar Atividade", bgcolor="#1B3A2C", color=COLOR_CONCLUIDA, on_click=handle_add_task)
                    ], alignment=ft.MainAxisAlignment.END, spacing=10)
                ], spacing=15, tight=True)
            )
        )
        page.dialog = add_dialog
        add_dialog.open = True
        page.update()

    def close_add_dialog(dlg):
        dlg.open = False
        page.update()

    # === ROTAS E NAVEGAÇÃO DE TELA (dynamic clean/render) ===
    def go_home(e):
        nonlocal current_category_filter
        current_category_filter = None
        page.clean()
        render_dashboard()

    def filter_by_class(class_key):
        nonlocal current_category_filter
        current_category_filter = class_key
        page.clean()
        
        class_alias = classes_names[class_key]
        
        # Header ajustado: apenas o ícone, o NOME DA CLASSE e o botão voltar
        workspace_header = ft.Row([
            ft.Row([
                ft.Container(
                    content=ft.Icon(ft.icons.HOME, color="purple", size=20),
                    border=ft.border.all(1, "purple"),
                    border_radius=5,
                    padding=5,
                    on_click=go_home
                ),
                ft.Text(f"{class_alias.upper()}", size=24, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY)
            ], spacing=10),
            ft.ElevatedButton(
                "← Voltar", 
                on_click=go_home, 
                bgcolor="blue", 
                color="white",
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6))
            )
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        update_tasks_view() # Preenche as tarefas apenas desta categoria

        top_content = ft.Column([
            workspace_header,
            ft.Divider(color="#222222", height=20),
            ft.Text(f"Exibindo tarefas de {class_alias}...", color=COLOR_TEXT_MUTED, size=12, italic=True),
            ft.Container(expand=True, content=tasks_container), # Lista apenas as filtradas
            ft.Divider(color="#222222", height=15),
            ft.Container(
                content=status_summary_row,
                bgcolor=COLOR_PANEL,
                border=ft.border.all(1, "#222222"),
                padding=14,
                border_radius=8
            )
        ], expand=True)

        main_layout = ft.Container(
            expand=True,
            padding=20,
            content=ft.Column(
                expand=True,
                controls=[top_content, footer]
            )
        )

        page.add(main_layout)
        page.update()

    def build_kpi_circles():
        items = []
        for cat_key, icon_cfg in CATEGORIES_CFG.items():
            count = len([t for t in tasks_db if t.category == cat_key])
            color = icon_cfg["color"]
            cat_alias = classes_names[cat_key]
            photo_url = classes_photos.get(cat_key)

            # Stack para sobrepor o texto de leitura sobre a foto circular de fundo
            circle_content = ft.Stack([
                ft.Container(
                    width=100,
                    height=100,
                    border_radius=50,
                    bgcolor="#111111",
                    image_src=photo_url,
                    image_fit=ft.ImageFit.COVER
                ),
                ft.Container(
                    width=100,
                    height=100,
                    border_radius=50,
                    bgcolor="rgba(10, 10, 10, 0.65)", # Filtro escuro para garantir nitidez do texto
                    border=ft.border.all(2, color if current_category_filter == cat_key else "#222222"),
                    alignment=ft.alignment.center,
                    content=ft.Column([
                        ft.Text(cat_alias.upper(), size=11, color=color, weight=ft.FontWeight.BOLD),
                        ft.Text(str(count), size=18, color=COLOR_TEXT_PRIMARY, weight=ft.FontWeight.W_850)
                    ], spacing=1, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                )
            ])

            items.append(
                ft.GestureDetector(
                    on_tap=lambda e, key=cat_key: filter_by_class(key),
                    mouse_cursor=ft.MouseCursor.CLICK,
                    content=circle_content
                )
            )
        return items

    # === CONSTRUÇÃO DO LAYOUT PRINCIPAL ===
    header = ft.Row([
        ft.Row([
            ft.Icon(ft.icons.HOME, size=24, color="purple"),
            ft.Text("Actividades", size=20, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY)
        ], spacing=10),
        ft.Row([
            ft.IconButton(
                icon=ft.icons.SETTINGS,
                icon_color="purple",
                tooltip="Configurar/Renomear Classes",
                on_click=open_settings
            ),
            ft.ElevatedButton(
                "Adicionar Tarefa",
                icon=ft.icons.ADD,
                bgcolor="#152B1E",
                color=COLOR_CONCLUIDA,
                on_click=open_add_task_dialog,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=6),
                    padding=ft.padding.symmetric(horizontal=16, vertical=12)
                )
            )
        ], spacing=12)
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    circles_row = ft.Row(
        controls=[],
        alignment=ft.MainAxisAlignment.SPACE_AROUND,
        spacing=8
    )

    def render_dashboard():
        circles_row.controls = build_kpi_circles()
        update_tasks_view()
        
        top_content = ft.Column([
            header,
            ft.Divider(color="#222222", height=20),
            active_filter_label,
            circles_row,
            ft.Divider(color="#222222", height=20),
            ft.Row([
                ft.Icon(ft.icons.REORDER_OUTLINED, size=18, color=COLOR_PENDENTE),
                ft.Text("LOGS DE EXECUÇÃO DA AGENDA (ALL)", size=13, weight=ft.FontWeight.BOLD, color=COLOR_TEXT_PRIMARY, font_family="monospace")
            ], spacing=6),
            ft.Container(expand=True, content=tasks_container),
            ft.Divider(color="#222222", height=15),
            ft.Container(
                content=status_summary_row,
                bgcolor=COLOR_PANEL,
                border=ft.border.all(1, "#222222"),
                padding=14,
                border_radius=8
            )
        ], expand=True)

        main_layout = ft.Container(
            expand=True,
            padding=20,
            content=ft.Column(
                expand=True,
                controls=[top_content, footer]
            )
        )

        page.add(main_layout)

    # Executa renderização inicial da dashboard
    render_dashboard()

if __name__ == "__main__":
    ft.app(target=main)
