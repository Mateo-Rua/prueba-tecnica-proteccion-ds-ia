"""Análisis de texto de las reseñas de Olist (comentarios en portugués).

Sin dependencias externas de NLP: limpieza con `unicodedata`, conteo de n-gramas
con `Counter` y clasificación por temas con expresiones regulares. La idea es que
el resultado sea auditable, no una caja negra.
"""

import re
import unicodedata
from collections import Counter

import pandas as pd

# Stopwords del portugués (artículos, preposiciones, pronombres y verbos vacíos).
STOPWORDS_PT = {
    "a", "ao", "aos", "aquela", "aquelas", "aquele", "aqueles", "aquilo", "as", "ate", "com",
    "como", "da", "das", "de", "dela", "delas", "dele", "deles", "depois", "do", "dos", "e",
    "ela", "elas", "ele", "eles", "em", "entre", "era", "eram", "essa", "essas", "esse",
    "esses", "esta", "estas", "este", "estes", "estou", "eu", "foi", "fomos", "for", "foram",
    "isso", "isto", "ja", "la", "lhe", "lhes", "mas", "me", "mesmo", "meu", "meus", "minha",
    "minhas", "muito", "na", "nao", "nas", "nem", "no", "nos", "nossa", "nosso", "num",
    "numa", "o", "os", "ou", "para", "pela", "pelas", "pelo", "pelos", "por", "qual",
    "quando", "que", "quem", "se", "sem", "ser", "seu", "seus", "so", "sua", "suas",
    "tambem", "te", "tem", "tenho", "ter", "teu", "tinha", "um", "uma", "voce", "voces",
    "vos", "ainda", "aqui", "esta", "estao", "ha", "vai", "sao", "pois", "ate", "mais",
}

# Diccionario de temas: cada patrón busca cómo se queja el cliente en portugués.
# Los `\b` evitan falsos positivos (p. ej. "corresponde" activando "responde").
TEMAS = {
    "entrega / retraso": (
        r"\batras|nao recebi|nao chegou|nao foi entregue|nao entregue|prazo|demor|"
        r"\bentreg|correio|transportadora|ainda nao|aguardando|nao veio|ate agora nada|"
        r"nao recebemos|nunca chegou|so recebi"
    ),
    "producto defectuoso / calidad": (
        r"defeito|defeituos|quebrad|danificad|estragad|qualidade|\bruim|pessim|"
        r"nao funciona|parou de funcionar|fragil|arranha|rasgad|amassad|velho|"
        r"nao presta|mal acabamento|vencid"
    ),
    "producto errado / incompleto": (
        r"errad|diferente|nao era|outro produto|veio outro|faltando|\bfaltou|\bfalta\b|"
        r"incomplet|so veio|veio apenas|recebi apenas|somente um|\bmetade\b|"
        r"nao corresponde|nao e o que|nao era o que"
    ),
    "atención / vendedor": (
        r"atendimento|\bresposta|\bresponde|\bcontato\b|comunica|vendedor|suporte|"
        r"ninguem|descaso|respeito|enrolad|\bloja\b"
    ),
    "reembolso / cancelación": (
        r"reembolso|estorno|dinheiro de volta|\bcancel|devolu|\btroca|garantia|"
        r"nota fiscal|estelionato|propaganda enganosa"
    ),
    "no cumple expectativas": (
        r"nao gostei|\bn gostei|nao recomendo|nao compre|decepcion|decepc|arrepend|"
        r"nao vale|nao e original|nao era oq|esperava|frustra|insatisf"
    ),
}

# Orden de prioridad cuando un comentario toca varios temas
PRIORIDAD_TEMAS = list(TEMAS)


def limpiar_texto(texto: str) -> str:
    """Minúsculas, sin tildes y sin signos: deja solo palabras comparables."""
    if not isinstance(texto, str):
        return ""
    texto = texto.lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(caracter for caracter in texto if not unicodedata.combining(caracter))
    texto = re.sub(r"[^a-z\s]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def tokenizar(texto: str, minimo_letras: int = 3) -> list[str]:
    """Palabras útiles de un comentario ya limpio (sin stopwords ni palabras muy cortas)."""
    return [
        palabra
        for palabra in texto.split()
        if palabra not in STOPWORDS_PT and len(palabra) >= minimo_letras
    ]


def top_ngramas(comentarios: pd.Series, n: int = 1, top: int = 15) -> pd.DataFrame:
    """Unigramas o bigramas más frecuentes en una serie de comentarios."""
    contador: Counter = Counter()
    for comentario in comentarios.dropna():
        tokens = tokenizar(limpiar_texto(comentario))
        if n == 1:
            contador.update(tokens)
        else:
            contador.update(
                " ".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1)
            )
    frecuencias = contador.most_common(top)
    return pd.DataFrame(frecuencias, columns=["expresion", "frecuencia"])


def clasificar_temas(resenas: pd.DataFrame, columna_texto: str = "review_comment_message") -> pd.DataFrame:
    """Marca qué temas aparecen en cada comentario (uno puede tener varios).

    Devuelve el `order_id`, una columna booleana por tema, el conteo de temas y el
    `tema_principal` según la prioridad definida.
    """
    base = resenas[resenas[columna_texto].notna()].copy()
    texto_limpio = base[columna_texto].map(limpiar_texto)

    marcas = pd.DataFrame({"order_id": base["order_id"].values})
    for tema, patron in TEMAS.items():
        marcas[tema] = texto_limpio.str.contains(patron, regex=True, na=False).values

    marcas["n_temas"] = marcas[list(TEMAS)].sum(axis=1)
    marcas["tema_principal"] = marcas.apply(_tema_principal, axis=1)
    marcas[columna_texto] = base[columna_texto].values
    return marcas


def _tema_principal(fila: pd.Series) -> str:
    """Primer tema según la prioridad; 'sin tema identificado' si no aplica ninguno."""
    for tema in PRIORIDAD_TEMAS:
        if fila[tema]:
            return tema
    return "sin tema identificado"


def resumen_temas(marcas: pd.DataFrame) -> pd.DataFrame:
    """% de comentarios negativos que menciona cada tema (no suma 100: hay solapamiento)."""
    total = len(marcas)
    filas = [
        {
            "tema": tema,
            "comentarios": int(marcas[tema].sum()),
            "pct_comentarios": marcas[tema].mean() * 100,
        }
        for tema in TEMAS
    ]
    sin_tema = (marcas["n_temas"] == 0).sum()
    filas.append({
        "tema": "sin tema identificado",
        "comentarios": int(sin_tema),
        "pct_comentarios": sin_tema / total * 100,
    })
    return pd.DataFrame(filas).sort_values("comentarios", ascending=False).round(2).reset_index(drop=True)


def ejemplos_por_tema(
    marcas: pd.DataFrame,
    tema: str,
    n: int = 3,
    max_palabras: int = 15,
    columna_texto: str = "review_comment_message",
) -> list[str]:
    """Comentarios cortos y representativos de un tema (en portugués original)."""
    candidatos = marcas[marcas[tema] & (marcas["n_temas"] == 1)][columna_texto]
    cortos = [texto.strip() for texto in candidatos if len(texto.split()) <= max_palabras]
    return cortos[:n]
