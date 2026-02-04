"""CLI 命令列工具

提供站點同步、資料庫初始化等命令列功能。
"""

import asyncio

import click

from app.database import SessionLocal, init_db
from app.services.cwa_sync import CWASyncService


@click.group()
def cli():
    """好日子 CLI 工具"""
    pass


@cli.command()
def sync_stations():
    """從 CWA API 同步站點資料"""
    click.echo("正在同步站點資料...")

    # 確保資料表存在
    init_db()

    with SessionLocal() as db:
        service = CWASyncService(db)
        result = asyncio.run(service.sync_stations())

    click.echo("同步完成！")
    click.echo(f"  取得站點數: {result['total_fetched']}")
    click.echo(f"  新增站點數: {result['created']}")
    click.echo(f"  更新站點數: {result['updated']}")


@cli.command()
def init_database():
    """初始化資料庫表"""
    click.echo("正在初始化資料庫...")
    init_db()
    click.echo("資料庫初始化完成！")


if __name__ == "__main__":
    cli()
