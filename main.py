import flet as ft
from datetime import datetime
import database as db

def main(page: ft.Page):
    page.title = "节流 APP"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    
    db.init_db()
    
    # --- UI 控件声明 ---
    balance_text = ft.Text("￥0.00", size=32, weight=ft.FontWeight.BOLD)
    budget_text = ft.Text("本月剩余额度: ￥0.00 / ￥0.00", size=14, color=ft.Colors.GREY_700)
    budget_progress = ft.ProgressBar(width=400, value=0, color=ft.Colors.BLUE, bgcolor=ft.Colors.GREY_300)
    
    records_list = ft.ListView(expand=1, spacing=10, padding=20)
    
    def refresh_ui():
        """刷新整个界面的数据呈现"""
        current_data = db.get_data()
        
        # 1. 【必须最先计算】计算本月总支出
        current_month = datetime.now().strftime("%Y-%m")
        total_expense = 0.0
        for r in current_data["records"]:
            if r["type"] == "支出" and r["date"].startswith(current_month):
                total_expense += r["amount"]
        # 2. 【有了总支出后，再算额度】大字展示“剩余额度”
        budget = current_data.get("budget", 0.0)
        remaining_budget = budget - total_expense
        
        balance_text.value = f"￥{remaining_budget:.2f}"
        balance_text.color = ft.Colors.GREEN_700 if remaining_budget >= 0 else ft.Colors.RED_700
        
        # 3. 刷新小字额度看板提示
        budget_text.value = f"本月已用: ￥{total_expense:.2f} | 剩余额度: ￥{remaining_budget:.2f} (总: ￥{budget:.2f})"
        
        
        if budget > 0:
            progress_value = total_expense / budget
            budget_progress.value = min(progress_value, 1.0) # 最高到 1.0
            budget_progress.color = ft.Colors.RED if progress_value > 0.8 else ft.Colors.BLUE
        else:
            budget_progress.value = 0
            budget_progress.color = ft.Colors.BLUE
            
        # 4. 刷新账单列表
        records_list.controls.clear()
        for r in current_data["records"]:
            is_income = r["type"] == "收入"
            records_list.controls.append(
                ft.ListTile(
                    leading=ft.Icon(
                        ft.Icons.ARROW_UPWARD if is_income else ft.Icons.ARROW_DOWNWARD,
                        color=ft.Colors.GREEN if is_income else ft.Colors.RED
                    ),
                    title=ft.Text(f"{r['category']} - {r['remark']}"),
                    subtitle=ft.Text(r['date']),
                    trailing=ft.Text(
                        f"{'+' if is_income else '-'}{r['amount']:.2f}",
                        weight=ft.FontWeight.BOLD,
                        size=16,
                        color=ft.Colors.GREEN if is_income else ft.Colors.RED
                    )
                )
            )
        page.update()

    # --- 弹窗 A：常规记账弹窗 ---
    type_radio = ft.RadioGroup(content=ft.Row([ft.Radio(value="支出", label="支出"), ft.Radio(value="收入", label="收入")]))
    type_radio.value = "支出"
    category_input = ft.TextField(label="分类(如: 餐饮、交通)", width=300)
    amount_input = ft.TextField(label="金额", prefix=ft.Text("￥"), keyboard_type=ft.KeyboardType.NUMBER, width=300)
    remark_input = ft.TextField(label="备注", width=300)

    def save_new_bill(e):
        if not amount_input.value or not category_input.value:
            return
        db.add_record(
            record_type=type_radio.value,
            category=category_input.value,
            amount=amount_input.value,
            remark=remark_input.value,
            date_str=datetime.now().strftime("%Y-%m-%d %H:%M")
        )
        category_input.value = ""
        amount_input.value = ""
        remark_input.value = ""
        dialog.open = False
        refresh_ui()

    dialog = ft.AlertDialog(
        title=ft.Text("记一笔账"),
        content=ft.Column([type_radio, category_input, amount_input, remark_input], tight=True, spacing=15),
        actions=[
            ft.TextButton("取消", on_click=lambda e: setattr(dialog, "open", False) or page.update()),
            ft.ElevatedButton("保存", on_click=save_new_bill, bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE)
        ]
    )
    page.overlay.append(dialog)

    # --- 弹窗 B：设置/提醒消费额度弹窗 ---
    budget_input = ft.TextField(label="输入本月消费额度", prefix=ft.Text("￥"), keyboard_type=ft.KeyboardType.NUMBER, width=300)
    
    def save_budget(e):
        if not budget_input.value:
            return
        this_month = datetime.now().strftime("%Y-%m")
        db.set_budget(budget_input.value, this_month)
        budget_dialog.open = False
        refresh_ui()

    budget_dialog = ft.AlertDialog(
        modal=True, # 强行拦截，必须输入或点取消
        title=ft.Text("💰 设置本月预算额度"),
        content=ft.Column([
            ft.Text("进入了新的月份或首次使用，请设置本月的消费预警额度：", size=14, color=ft.Colors.GREY_600),
            budget_input
        ], tight=True, spacing=10),
        actions=[
            ft.TextButton("暂不设置", on_click=lambda e: setattr(budget_dialog, "open", False) or page.update()),
            ft.ElevatedButton("确认设置", on_click=save_budget, bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE)
        ]
    )
    page.overlay.append(budget_dialog)

    # --- 自动检测：是否需要弹出额度输入提示（如每月1号或新月份首次打开） ---
    def check_monthly_budget_prompt():
        current_data = db.get_data()
        this_month = datetime.now().strftime("%Y-%m")
        # 如果保存的预算月份和当前月份不一致，说明跨月了（或者首次使用），自动弹窗提醒
        if current_data.get("budget_month") != this_month:
            budget_dialog.open = True
            page.update()

    # --- 主界面布局 ---
    page.add(
        # 顶部资产 & 额度卡片
        ft.Container(
            content=ft.Column([
                ft.Text("本月剩余可用额度", size=13, color=ft.Colors.GREY_600, weight=ft.FontWeight.BOLD),
                balance_text,
                ft.Container(height=10),
                budget_text,
                budget_progress,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            margin=20,
            padding=20,
            bgcolor=ft.Colors.GREY_100,
            border_radius=15,
            alignment=ft.Alignment(0, 0)
        ),
        ft.Divider(height=1),
        # 账单历史列表
        ft.Container(content=records_list, expand=True)
    )
    
    page.floating_action_button = ft.FloatingActionButton(
        content=ft.Row([ft.Icon(ft.Icons.ADD, color=ft.Colors.WHITE), ft.Text("记账", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.CENTER, spacing=5),
        width=100, bgcolor=ft.Colors.BLUE,
        on_click=lambda e: setattr(dialog, "open", True) or page.update()
    )
    
    # 首次加载与检测
    refresh_ui()
    check_monthly_budget_prompt()

if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.FLET_APP)