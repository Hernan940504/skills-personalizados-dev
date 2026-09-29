"""Clasificación de correos por criticidad y redacción de datos sensibles.

No usa red: opera sobre headers (From/Subject/To) y el snippet corto que provee Gmail. Decide si un
correo es de criticidad **alta** (se indexa como nota), **media** (entra a la bitácora del proyecto)
o **baja** (se ignora), y detecta compromisos dirigidos al usuario. Antes de escribir cualquier
texto al vault, enmascara patrones de secretos/PII.

Las reglas son listas configurables para poder afinarlas sin tocar la lógica.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# --- Reglas configurables ----------------------------------------------------

# Remitentes/patrones de ruido → criticidad baja (se ignora).
NOISE_SENDER_PATTERNS = [
    r"no[-_.]?reply", r"noreply", r"notifications?@", r"newsletter", r"mailer-daemon",
    r"jira@", r"@atlassian", r"datadog", r"alerts?@", r"bounce", r"marketing@",
    r"automat", r"do[-_.]?not[-_.]?reply", r"@calendar", r"invitaci[oó]n", r"confluence",
    r"sonarcloud", r"github\.com", r"aws-marketing", r"@google", r"workflow",
    # newsletters / boletines de productos externos (SaaS marketing)
    r"@mail\.", r"@e\.read\.ai", r"@notion\.so", r"read\.ai", r"@customer\.io",
    r"@comunicaciones", r"@news\.", r"@email\.", r"@hello\.", r"@marketing\.",
]
NOISE_SUBJECT_PATTERNS = [
    r"\bnewsletter\b", r"\bunsubscribe\b", r"\bboletín\b", r"\bpromoci[oó]n\b",
    r"\b\[JIRA\]\b", r"\bbuild (passed|failed)\b", r"\bdigest\b", r"\binvitaci[oó]n\b",
    r"\baceptad[ao]\b", r"\brechazad[ao]\b", r"\brecordatorio\b", r"\bencuesta\b",
    r"\bfuera de la oficina\b", r"\bout of office\b", r"\bautomat", r"\bactualizaci[oó]n de estado\b",
]

# Señales FUERTES: bastan por sí solas para elevar a alta (eventos inequívocos).
STRONG_SIGNAL_PATTERNS = [
    r"\bincidente\b", r"\boutage\b", r"\bca[ií]da (de|del|en)\b", r"\bfuera de servicio\b",
    r"\bdecisi[oó]n (de|sobre|arquitect)", r"\bacuerdo (firmado|final|de)\b",
    r"\baprobaci[oó]n (de|del|final)\b", r"\bfecha l[ií]mite\b", r"\bdeadline\b",
    r"\bley 2300\b", r"\bpost[- ]?mortem\b", r"\bbrecha de seguridad\b", r"\bvulnerabilidad cr[ií]tica\b",
]

# Señales DÉBILES: por sí solas NO elevan; requieren >=2 (o combinarse con contexto) para ser alta.
WEAK_SIGNAL_PATTERNS = [
    r"\barquitectura\b", r"\bproducci[oó]n\b", r"\bmigraci[oó]n\b", r"\bacceso[s]?\b",
    r"\bcredencial(es)?\b", r"\binfraestructura\b", r"\bpol[ií]tica\b", r"\burgente\b",
    r"\bcr[ií]tico\b", r"\baprobaci[oó]n\b", r"\bacuerdo\b", r"\bdecisi[oó]n\b",
]

# Verbos/expresiones de compromiso dirigido a quien lee (→ alta).
COMMITMENT_PATTERNS = [
    r"\bqued[aá]s? (encargad|a cargo)", r"\bte asign",
    r"\bnecesito que\b.*\b(env[ií]es|revises|valides|confirmes|entregues|hagas|generes|subas|prepares)\b",
    r"\bpor favor\b.*\b(env[ií]a|revisa|valida|confirma|entrega|haz)\b",
    r"\bpendiente (tuyo|de ti|para ti)\b", r"\bte encargo\b",
    r"\bte (queda|dejo) (el|la|los|las|de)\b", r"\bqued[oó] (a tu cargo|en ti)\b",
    r"\bespero tu (respuesta|confirmaci[oó]n|apoyo)\b",
]

# Patrones de secretos/PII a enmascarar antes de indexar.
SECRET_PATTERNS = [
    (re.compile(r"(?i)((?:api[-_ ]?key|apikey|token|secret|password|contrase[nñ]a)\s*[:=]\s*)\S+"), r"\1<redacted>"),
    (re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]+"), "bearer <redacted>"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "<redacted-aws-key>"),
    (re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----"), "<redacted-private-key>"),
    (re.compile(r"\b\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{4}\b"), "<redacted-card>"),
]


@dataclass
class Classification:
    """Resultado de clasificar un correo."""

    level: str  # "alta" | "media" | "baja"
    reasons: list[str] = field(default_factory=list)
    commitment: str | None = None


def _any(patterns: list[str], text: str) -> str | None:
    for p in patterns:
        if re.search(p, text, re.IGNORECASE):
            return p
    return None


def _count(patterns: list[str], text: str) -> list[str]:
    """Devuelve los patrones (distintos) que coinciden en el texto."""
    return [p for p in patterns if re.search(p, text, re.IGNORECASE)]


def detect_commitment(text: str) -> str | None:
    """Devuelve una frase de compromiso si el texto la contiene, o None."""
    for p in COMMITMENT_PATTERNS:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            start = max(0, m.start() - 20)
            end = min(len(text), m.end() + 60)
            return text[start:end].strip()
    return None


def classify(sender: str, subject: str, snippet: str, *, user_email: str = "",
             recipients: str = "") -> Classification:
    """Clasifica un correo en alta/media/baja.

    :param sender: valor del header ``From``.
    :param subject: asunto.
    :param snippet: extracto corto (no el cuerpo completo).
    :param user_email: correo del usuario (para detectar menciones/compromisos dirigidos).
    :param recipients: valor del header ``To``/``Cc`` (para ver si el usuario está en directo).
    :return: ``Classification`` con nivel, motivos y compromiso detectado.
    """
    haystack = f"{subject}\n{snippet}"
    reasons: list[str] = []

    # 1) Ruido → baja (salvo que haya un compromiso dirigido explícito).
    noise = _any(NOISE_SENDER_PATTERNS, sender) or _any(NOISE_SUBJECT_PATTERNS, subject)

    # 2) Compromiso dirigido al usuario → alta. Requiere que el usuario esté direccionado
    #    (en To/Cc o mencionado en el texto); si no se conoce el usuario, no se asume compromiso.
    commitment = None
    user_addressed = bool(user_email) and (
        user_email.lower() in recipients.lower() or user_email.lower() in haystack.lower()
    )
    if user_addressed:
        commitment = detect_commitment(haystack)
    if commitment:
        reasons.append("compromiso-dirigido")
        return Classification(level="alta", reasons=reasons, commitment=commitment)

    if noise:
        return Classification(level="baja", reasons=[f"ruido:{noise}"])

    # 3) Señal FUERTE → alta directa (evento inequívoco).
    strong = _any(STRONG_SIGNAL_PATTERNS, haystack)
    if strong:
        reasons.append(f"senal-fuerte:{strong}")
        return Classification(level="alta", reasons=reasons)

    # 4) Señales DÉBILES: 2 o más distintas → alta; una sola → media.
    weak = _count(WEAK_SIGNAL_PATTERNS, haystack)
    if len(weak) >= 2:
        reasons.append("senales-debiles:" + ",".join(weak[:3]))
        return Classification(level="alta", reasons=reasons)
    if weak:
        reasons.append(f"senal-debil:{weak[0]}")
        return Classification(level="media", reasons=reasons)

    # 5) Resto de la línea de negocio → media.
    return Classification(level="media", reasons=["contexto-linea-negocio"])


def redact(text: str) -> str:
    """Enmascara secretos/PII conocidos en un texto antes de indexarlo."""
    out = text
    for pattern, repl in SECRET_PATTERNS:
        out = pattern.sub(repl, out)
    return out


_LEVEL_RANK = {"baja": 0, "media": 1, "alta": 2}


def classify_thread(thread: dict, *, user_email: str = "") -> tuple[Classification, dict]:
    """Clasifica un hilo por la criticidad MÁXIMA entre sus mensajes.

    :param thread: hilo de ``gmail_client.get_thread``.
    :param user_email: correo del usuario (para compromisos dirigidos).
    :return: ``(Classification del hilo, mensaje representativo que disparó el nivel)``.
    """
    best = Classification(level="baja", reasons=["hilo-vacio"])
    best_msg = thread["messages"][0] if thread.get("messages") else {}
    for msg in thread.get("messages", []):
        texto = msg.get("body") or msg.get("snippet", "")
        c = classify(msg.get("sender", ""), msg.get("subject", ""), texto,
                     user_email=user_email, recipients=msg.get("to", ""))
        if _LEVEL_RANK[c.level] > _LEVEL_RANK[best.level]:
            best, best_msg = c, msg
            if c.level == "alta":
                break
    return best, best_msg


def clean_body(text: str, *, max_chars: int = 1500) -> str:
    """Limpia el cuerpo de un correo para indexarlo: quita citas/firmas triviales, redacta y acota.

    :param text: cuerpo de texto plano.
    :param max_chars: tope de caracteres a conservar.
    :return: texto saneado (redactado) listo para la nota; cadena vacía si no queda contenido útil.
    """
    if not text:
        return ""
    # Marcadores donde el contenido útil TERMINA: aviso legal, firmas, inicio de la cita del
    # mensaje anterior. Se corta ahí para no arrastrar disclaimers ni cadenas de respuestas.
    cut_markers = [
        r"aviso legal", r"este mensaje es confidencial", r"confidentiality notice",
        r"\bEl .*escribi[oó]:", r"\bOn .*wrote:", r"-{2,}\s*mensaje reenviado",
        r"^--\s*$",
    ]
    lines = []
    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if any(re.search(m, stripped, re.IGNORECASE) for m in cut_markers):
            break  # fin del contenido útil
        if stripped.startswith(">"):
            continue
        if re.match(r"(?i)^(from:|de:|enviado el:|sent:|para:|to:|cc:|asunto:|subject:)", stripped):
            continue
        lines.append(line)
    cleaned = "\n".join(lines).strip()
    cleaned = redact(cleaned)
    if len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars].rsplit(" ", 1)[0] + " […]"
    return cleaned


def summarize_thread(thread: dict, cls: Classification, best_msg: dict) -> str:
    """Arma el cuerpo Markdown de la nota de un hilo (contenido real, redactado).

    Devuelve cadena vacía si no hay contenido útil (para no crear notas basura).
    """
    cuerpo = clean_body(best_msg.get("body") or best_msg.get("snippet", ""))
    if not cuerpo:
        return ""
    participantes = ", ".join(redact(p) for p in thread.get("participants", [])[:8])
    n_msgs = len(thread.get("messages", []))
    compromiso = f"\n## Compromiso detectado\n- {redact(cls.commitment)}\n" if cls.commitment else ""
    return (
        f"## Hilo de correo (criticidad {cls.level})\n"
        f"- Asunto: {redact(thread.get('subject', ''))}\n"
        f"- Participantes: {participantes}\n"
        f"- Mensajes en el hilo: {n_msgs}\n"
        f"- Mensaje clave de: {redact(best_msg.get('sender', ''))} · {best_msg.get('date', '')}\n"
        f"- Motivos: {', '.join(cls.reasons)}\n"
        f"- Enlace: {thread.get('thread_url', '')}\n"
        f"{compromiso}"
        f"\n## Contenido\n{cuerpo}\n"
    )
