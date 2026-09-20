"""Funciones auxiliares comunes: formato, gráficos y checklist de validación."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.data_loader import RUTA_PROYECTO

RUTA_FIGURAS = RUTA_PROYECTO / "reports" / "figures"
RUTA_TABLAS = RUTA_PROYECTO / "reports" / "tables"

# Un solo tono para series únicas; el segundo resalta la barra líder.
COLOR_BARRA = "#3d7ab8"
COLOR_DESTACADO = "#1f4e79"
COLOR_TEXTO = "#333333"


def formato_moneda(valor: float) -> str:
    """R$ con separador de miles en formato colombiano/brasileño (1.234.567)."""
    return "R$ " + f"{valor:,.0f}".replace(",", ".")


def formato_miles(valor: float) -> str:
    return f"{valor:,.0f}".replace(",", ".")


def grafico_barras_horizontal(
    datos: pd.DataFrame,
    columna_categoria: str,
    columna_valor: str,
    columna_porcentaje: str,
    titulo: str,
    subtitulo: str,
    es_moneda: bool,
    nombre_archivo: str,
    ruta_figuras: Path = RUTA_FIGURAS,
) -> Path:
    """Barras horizontales ordenadas, con el valor y el % etiquetados en cada barra."""
    datos = datos.sort_values(columna_valor)  # la barra mayor queda arriba
    etiquetas = datos[columna_categoria]
    valores = datos[columna_valor]
    formato = formato_moneda if es_moneda else formato_miles

    fig, ax = plt.subplots(figsize=(10, 5))
    colores = [COLOR_BARRA] * len(datos)
    colores[-1] = COLOR_DESTACADO  # la categoría líder
    barras = ax.barh(etiquetas, valores, color=colores, height=0.62)

    for barra, valor, porcentaje in zip(barras, valores, datos[columna_porcentaje]):
        ax.text(
            barra.get_width() + valores.max() * 0.015,
            barra.get_y() + barra.get_height() / 2,
            f"{formato(valor)}  ({porcentaje:.1f}%)",
            va="center",
            fontsize=10,
            color=COLOR_TEXTO,
        )

    ax.set_xlim(0, valores.max() * 1.28)
    ax.set_xticks([])
    ax.tick_params(axis="y", length=0, labelsize=11)
    for lado in ("top", "right", "bottom", "left"):
        ax.spines[lado].set_visible(False)

    ax.set_title(titulo, fontsize=14, fontweight="bold", loc="left", pad=22, color=COLOR_TEXTO)
    ax.text(0, 1.03, subtitulo, transform=ax.transAxes, fontsize=10, color="#666666")

    ruta_figuras.mkdir(parents=True, exist_ok=True)
    ruta_salida = ruta_figuras / nombre_archivo
    plt.tight_layout()
    plt.savefig(ruta_salida, dpi=150, bbox_inches="tight")
    plt.show()
    return ruta_salida


def grafico_barras_vertical(
    datos: pd.DataFrame,
    columna_categoria: str,
    columna_valor: str,
    titulo: str,
    subtitulo: str,
    nombre_archivo: str,
    sufijo_valor: str = "%",
    ruta_figuras: Path = RUTA_FIGURAS,
) -> Path:
    """Barras verticales en el orden dado, con el valor etiquetado encima."""
    etiquetas = datos[columna_categoria]
    valores = datos[columna_valor]

    fig, ax = plt.subplots(figsize=(9, 5))
    colores = [COLOR_BARRA] * len(datos)
    colores[int(valores.values.argmax())] = COLOR_DESTACADO
    barras = ax.bar(etiquetas, valores, color=colores, width=0.62)

    for barra, valor in zip(barras, valores):
        ax.text(
            barra.get_x() + barra.get_width() / 2,
            barra.get_height() + valores.max() * 0.02,
            f"{valor:.1f}{sufijo_valor}",
            ha="center",
            fontsize=10,
            color=COLOR_TEXTO,
        )

    ax.set_ylim(0, valores.max() * 1.18)
    ax.set_yticks([])
    ax.tick_params(axis="x", length=0, labelsize=11)
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.spines["bottom"].set_color("#cccccc")

    ax.set_title(titulo, fontsize=14, fontweight="bold", loc="left", pad=22, color=COLOR_TEXTO)
    ax.text(0, 1.03, subtitulo, transform=ax.transAxes, fontsize=10, color="#666666")

    ruta_figuras.mkdir(parents=True, exist_ok=True)
    ruta_salida = ruta_figuras / nombre_archivo
    plt.tight_layout()
    plt.savefig(ruta_salida, dpi=150, bbox_inches="tight")
    plt.show()
    return ruta_salida


def imprimir_checklist(validaciones: list[tuple[str, bool, str]]) -> bool:
    """Imprime ✅/❌ por validación y devuelve True si todas pasaron."""
    print("CHECKLIST DE VALIDACIÓN")
    print("-" * 70)
    for descripcion, resultado, detalle in validaciones:
        print(f"{'✅' if resultado else '❌'} {descripcion}: {detalle}")
    todas_ok = all(resultado for _, resultado, _ in validaciones)
    print("-" * 70)
    print("TODAS LAS VALIDACIONES PASARON" if todas_ok else "HAY VALIDACIONES FALLIDAS")
    return todas_ok


def guardar_tabla(datos: pd.DataFrame, nombre_archivo: str, ruta_tablas: Path = RUTA_TABLAS) -> Path:
    """Guarda una tabla en reports/tables/ en CSV UTF-8."""
    ruta_tablas.mkdir(parents=True, exist_ok=True)
    ruta_salida = ruta_tablas / nombre_archivo
    datos.to_csv(ruta_salida, index=False, encoding="utf-8-sig")
    return ruta_salida
