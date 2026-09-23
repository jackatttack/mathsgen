"""Presentation grouping and colours, independent of Pythonista and generators."""

TOPICS = {
    "number": ("Number", "#2563EB", "#EAF1FF"),
    "algebra": ("Algebra", "#7C3AED", "#F1EBFF"),
    "ratio": ("Ratio & proportion", "#087F8C", "#E4F5F5"),
    "geometry": ("Geometry & measures", "#B45309", "#FFF1DE"),
    "probability": ("Probability", "#BE185D", "#FCE8F1"),
    "data": ("Statistics", "#15803D", "#E8F5EC"),
    "problem_solving": ("Problem solving", "#0F766E", "#DCF5EF"),
}
ORDER = tuple(TOPICS)


def topic_style(topic):
    return TOPICS.get(topic, (topic.replace("_", " ").title(), "#475569", "#EDF1F5"))


def group_name(info):
    parts = info.id.split(".")
    if info.topic == "algebra":
        if "quadratic" in parts:
            return "Quadratics"
        if "graphs" in parts:
            return "Straight lines & graphs"
        if "sequences" in parts:
            return "Sequences"
        if "simultaneous" in parts:
            return "Simultaneous equations"
        if "linear" in parts:
            return "Linear equations"
        if "rearranging" in parts:
            return "Changing the subject"
        if "expanding" in parts or "factorising" in parts:
            return "Expanding & factorising"
    if info.topic == "number":
        names = {
            "fractions": "Fractions", "fdp": "Fractions, decimals & percentages",
            "percentages": "Percentages", "indices": "Indices",
            "standard_form": "Standard form",
            "rounding": "Rounding & estimation", "estimation": "Rounding & estimation",
            "bounds": "Bounds", "compound": "Compound measures",
            "primes": "Factors, multiples & primes", "factors": "Factors, multiples & primes",
            "multiples": "Factors, multiples & primes",
        }
        if len(parts) > 1 and parts[1] in names:
            return names[parts[1]]
    if info.topic == "ratio":
        return "Direct & inverse proportion" if "proportion" in parts else "Ratio"
    if info.topic == "data":
        return "Averages & spread" if any(p in parts for p in ("mean", "averages")) else "Charts & data"
    if info.topic == "probability":
        return "Repeated events" if "two_draws" in parts else "Single events"
    if info.topic == "geometry":
        names = {"angles": "Angles", "pythagoras": "Pythagoras", "area": "Area"}
        if len(parts) > 1 and parts[1] in names:
            return names[parts[1]]
    return info.subtopic.replace("_", " ").title()


def groups_for(infos):
    buckets = {}
    for info in infos:
        name = group_name(info)
        key = info.topic + "/" + name
        if key not in buckets:
            buckets[key] = {"key": key, "topic": info.topic, "title": name, "infos": []}
        buckets[key]["infos"].append(info)

    def order(group):
        topic = group["topic"]
        return (ORDER.index(topic) if topic in ORDER else len(ORDER), topic, group["title"])

    groups = sorted(buckets.values(), key=order)
    for group in groups:
        group["infos"].sort(key=lambda info: (info.title.casefold(), info.id))
    return groups


def matches(info, query):
    topic_title = topic_style(info.topic)[0]
    text = " ".join((
        info.title, info.id.replace("_", " "), info.subtopic.replace("_", " "),
        topic_title, group_name(info), " ".join(info.tags),
    )).casefold()
    return all(word in text for word in query.casefold().split())