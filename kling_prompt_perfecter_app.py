import streamlit as st
import re, json

st.set_page_config(page_title="Kling Prompt Perfecter", page_icon="✨", layout="centered")

st.title("✨ Kling Prompt Perfecter")
st.write("Paste your rich, cinematic scene text and get a short, structured, Kling-friendly prompt.")

# -----------------------------
# Utilities
# -----------------------------
def _kw(*items):
    return set([i.lower() for i in items])

def find_terms(text, vocab):
    found = []
    t = text.lower()
    for term in sorted(vocab, key=lambda x: -len(x)):
        if re.search(rf'(?<!\w){re.escape(term)}(?!\w)', t):
            found.append(term)
    ordered = []
    for term in found:
        if term not in ordered:
            ordered.append(term)
    return ordered

def proper_names(text):
    names = []
    for line in re.split(r'[\n]', text):
        tokens = re.findall(r"\b[A-Z][a-zA-Z'-]+\b", line)
        for tok in tokens:
            if tok not in names:
                names.append(tok)
    return names

def compress_list(items, max_items):
    return items[:max_items] if max_items and max_items > 0 else items

def build_prompt(sections, mode="standard", use_labels=True):
    lines = []
    for label, content in sections:
        if not content:
            continue
        if isinstance(content, (list, tuple)):
            text = ", ".join(content)
        else:
            text = str(content)
        if use_labels:
            lines.append(f"{label}: {text}")
        else:
            lines.append(text)
    if mode == "concise":
        lines = [re.sub(r"\b(a|an|the)\b ", "", ln, flags=re.I) for ln in lines]
    elif mode == "verbose":
        lines = [ln.replace(": ", ": ").replace(",", ", ") for ln in lines]
    return "\n".join(lines)

# -----------------------------
# Base vocabulary (broad domains)
# -----------------------------
CHAR_ROLES = _kw(
    "alchemist","warrior","mage","knight","mechanic","inventor","scholar","assassin","archer",
    "priest","monk","sailor","pirate","captain","soldier","guard","queen","king","prince","princess",
    "villager","merchant","scientist","engineer","android","cyborg","child","boy","girl","man","woman",
    "elder","apprentice","master","mentor","student","teacher","hunter","ranger","witch","wizard","samurai",
    "detective","hacker","pilot","smuggler","ranger","bard","cleric","vampire","occultist"
)

CLOTHING = _kw(
    "coat","cloak","robe","hood","hooded","cape","armor","breastplate","gauntlets","boots","sandals",
    "gloves","mask","goggles","scarf","belt","tunic","dress","skirt","trousers","pants","jacket",
    "tattered","ragged","silk","leather","linen","chainmail","kimono","trench coat","fedora"
)

PHYS_ATTR = _kw(
    "tall","short","lean","muscular","slim","stocky","scarred","freckled","tattooed","bearded",
    "bald","long hair","short hair","silver hair","black hair","blonde hair","red hair","brown hair",
    "blue eyes","green eyes","brown eyes","grey eyes","golden eyes","sharp eyes","pale skin"
)

OBJECTS = _kw(
    "sword","dagger","book","tome","scroll","pocketwatch","watch","gear","gears","cog","lantern",
    "lamp","staff","wand","potion","vial","flask","orb","crystal","compass","map","quill","feather",
    "hammer","wrench","tool","tools","machine","device","bracelet","amulet","ring","necklace",
    "chain","clock","hourglass","violin","gun","rifle","blaster","drone","camera","smartphone"
)

ENVIRONMENTS = _kw(
    "workshop","lab","laboratory","library","forge","factory","market","alley","street","castle","throne room",
    "dungeon","forest","woods","jungle","desert","oasis","cave","mountain","cliff","harbor","port","ship","deck",
    "sky","clouds","city","village","ruins","temple","cathedral","church","graveyard","garden","field","meadow",
    "river","lake","waterfall","swamp","sewer","tower","observatory","cafe","apartment","park","train station"
)

TIME_OF_DAY = _kw("dawn","sunrise","morning","noon","afternoon","sunset","twilight","dusk","night","midnight","golden hour")
WEATHER = _kw("rain","storm","snow","fog","mist","smoke","wind","windy","thunder","lightning","dust","sandstorm","smog")

LIGHTING = _kw(
    "light","lit","glow","glowing","illumination","highlight","rim light","backlight","backlit","lantern light",
    "torchlight","candlelight","neon","bioluminescent","sunbeam","god rays","volumetric light","soft light",
    "hard light","contrast","shadow","shadows","dramatic shadows","low key","high key","silhouette","moonlight"
)

COLORS = _kw(
    "gold","golden","amber","orange","red","crimson","scarlet","pink","magenta","purple","violet","blue",
    "cyan","teal","green","emerald","lime","yellow","warm","cool","monochrome","sepia","brass","copper","silver"
)

CAMERA = _kw(
    "close-up","close up","extreme close-up","portrait","bust","mid-shot","medium shot","cowboy shot",
    "wide shot","long shot","establishing shot","low angle","high angle","bird's-eye view","top-down",
    "over-the-shoulder","dutch angle","tilt","pan","tracking shot","depth of field","bokeh","rule of thirds","centered"
)

COMPOSITION = _kw(
    "symmetry","asymmetry","leading lines","foreground","midground","background","negative space",
    "framing","vignette","dynamic pose","profile","three-quarter view","silhouette"
)

MOOD = _kw(
    "tense","mysterious","ominous","melancholic","somber","hopeful","serene","epic","dramatic",
    "whimsical","romantic","grim","triumphant","anxious","calm","chaotic","majestic","mournful","noir","nostalgic"
)

STYLE = _kw(
    "anime","motion graphics","cinematic","cell shaded","cel-shaded","manga","illustration","hand-drawn",
    "comic","realistic","photoreal","painterly","watercolor","oil painting","ink","line art","cyberpunk","steampunk"
)

QUALITY = _kw(
    "highly detailed","ultra detailed","sharp focus","crisp lines","4k","uhd","hdr","global illumination","film grain"
)

EFFECTS = _kw("sparks","embers","smoke","steam","dust","particles","glitter","rain droplets","snowflakes","lens flare","glitches")

# -----------------------------
# Style Presets (expanded)
# -----------------------------
STYLE_PRESETS = {
    "Motion Graphics Anime (default)": ["cinematic","anime","motion graphics","highly detailed","dramatic shadows","crisp lines"],
    "Cel-Shaded Anime": ["anime","cel-shaded","clean line art","bold shadows","saturated color"],
    "Realistic Cinematic": ["cinematic","realistic","volumetric light","film grain","hdr"],
    "Painterly Fantasy": ["painterly","soft brushwork","textured canvas","romantic lighting"],
    "Manga Ink": ["manga","ink","line art","screentone","high contrast"],
    "Shōnen Action Anime": ["anime","dynamic pose","speedlines","high contrast","saturated color"],
    "Studio Ghibli Soft": ["painterly","soft edges","warm palette","natural light","gentle shading"],
    "Manga Black & White": ["black and white","high contrast","inked lines","screentone"],
    "Watercolor Illustration": ["watercolor","soft gradients","paper texture","pastel palette"],
    "Film Noir Cinematic": ["black and white","low key","venetian blinds","hard contrast","grain"],
    "Golden Age Hollywood": ["cinematic","technicolor palette","glamour lighting","film grain"],
    "Ultra-Realistic 3D Render": ["photoreal","raytracing","global illumination","sharp focus","hdr"],
    "Documentary Natural Light": ["handheld feel","natural light","minimal grading","realistic"],
    "Cyberpunk Neon": ["cyberpunk","neon glow","rain reflections","holographic spill","high contrast"],
    "Retro Sci-Fi Pulp": ["pulp illustration","halftone","flat colors","retro futurism"],
    "Synthwave / Vaporwave": ["retro","neon gradient","gridlines","glow","80s aesthetic"],
    "Mecha Anime": ["anime","mechanical precision","metallic texture","dramatic low angle"],
    "Steampunk Illustration": ["steampunk","sepia tint","brass and copper","industrial shading"],
    "Dieselpunk Grit": ["gritty","smoky atmosphere","muted palette","industrial"],
    "Pop Art Comic": ["bold outlines","halftone dots","primary colors","comic frame"],
    "Surrealist Dreamscape": ["surreal","warped perspective","dreamlike lighting","ethereal"],
    "Mythic African Epic": ["bold patterns","earthy palette","spiritual glow","ceremonial motifs"],
    "Celestial Cosmic Fantasy": ["cosmic nebulae","glow","ethereal","starfields"]
}

# -----------------------------
# Story Packs (built-in + expanded)
# -----------------------------
STORY_PACKS = {
    "General (Default)": {k: [] for k in ["CHAR_ROLES","CLOTHING","PHYS_ATTR","OBJECTS","ENVIRONMENTS","TIME_OF_DAY","WEATHER","LIGHTING","COLORS","CAMERA","COMPOSITION","MOOD","STYLE","QUALITY","EFFECTS"]},
    "The Clockwork Alchemist": {
        "CHAR_ROLES": ["alchemist","mechanist","guildmaster","automaton","clockmaker","airship captain","apprentice"],
        "CLOTHING": ["brass goggles","mechanical gauntlet","leather harness","tattered coat","oil-stained gloves","clockwork prosthetic"],
        "PHYS_ATTR": ["soot-smudged","grease-streaked","silver hair","sharp eyes"],
        "OBJECTS": ["brass pocketwatch","ether vial","alchemical sigil","rune plate","spring coil","pressure gauge","gearwork heart","steam valve","arc lamp"],
        "ENVIRONMENTS": ["clockwork workshop","gilded laboratory","observatory tower","airship deck","steamworks","gear hall","cobblestone alley","ruined cathedral","boiler room"],
        "TIME_OF_DAY": ["gaslamp night","dawn fog"],
        "WEATHER": ["sooty haze","steam plume","industrial fog"],
        "LIGHTING": ["lantern glow","arc light","flicker light","volumetric steam light"],
        "COLORS": ["brass","copper","verdigris","oil-sheen"],
        "CAMERA": ["close-up","mid-shot","wide shot","low angle","high angle","over-the-shoulder","dutch angle"],
        "COMPOSITION": ["foreground gears","backlit silhouette","leading lines of pipes"],
        "MOOD": ["tense","mysterious","epic","melancholic","triumphant"],
        "STYLE": ["steampunk","anime","cinematic"],
        "QUALITY": ["highly detailed","crisp lines","4k","dramatic shadows"],
        "EFFECTS": ["sparks","embers","steam","dust motes"]
    },
    "Neon Sci-Fi / Cyberpunk": {
        "CHAR_ROLES": ["netrunner","android","street samurai","corporate agent","hacker","detective"],
        "CLOTHING": ["neon jacket","visored helmet","techwear cloak","fiber-optic hair","chrome prosthetic"],
        "PHYS_ATTR": ["augmented eyes","cybernetic arm","holographic tattoos"],
        "OBJECTS": ["neon katana","data shard","holo-screen","drone","plasma pistol","aug rig"],
        "ENVIRONMENTS": ["rain-soaked alley","rooftop skyline","arcology lobby","night market","megacity block"],
        "TIME_OF_DAY": ["night","dawn"],
        "WEATHER": ["rain","mist","smog"],
        "LIGHTING": ["neon glow","backlit signage","hologram spill"],
        "COLORS": ["magenta","cyan","electric blue","acid green"],
        "CAMERA": ["low angle","wide shot","over-the-shoulder","close-up"],
        "COMPOSITION": ["reflections in puddles","crowded background","silhouette in signage"],
        "MOOD": ["tense","noir","rebellious","grim"],
        "STYLE": ["cyberpunk","anime","cinematic"],
        "QUALITY": ["highly detailed","hdr","crisp lines"],
        "EFFECTS": ["rain droplets","steam","glitches","lens flare"]
    },
    "Medieval High Fantasy": {
        "CHAR_ROLES": ["knight","sorceress","ranger","bard","cleric","dragon","queen","king","orc","elf"],
        "CLOTHING": ["plate armor","chainmail","tabard","hooded cloak","wizard robe","leather boots"],
        "PHYS_ATTR": ["pointed ears","scarred","braided hair","emerald eyes"],
        "OBJECTS": ["longsword","spellbook","crystal staff","enchanted bow","shield","chalice"],
        "ENVIRONMENTS": ["castle hall","enchanted forest","mountain pass","ancient ruins","village square"],
        "TIME_OF_DAY": ["dawn","sunset","night"],
        "WEATHER": ["fog","snow","storm"],
        "LIGHTING": ["torchlight","moonlight","sunbeams","god rays"],
        "COLORS": ["emerald","gold","crimson","sapphire"],
        "CAMERA": ["establishing shot","low angle","wide shot","close-up"],
        "COMPOSITION": ["leading lines","foreground foliage","backlit silhouette"],
        "MOOD": ["epic","mystical","hopeful","ominous"],
        "STYLE": ["anime","painterly","cinematic"],
        "QUALITY": ["highly detailed","4k","dramatic shadows"],
        "EFFECTS": ["embers","dust motes","sparkles","magic particles"]
    },
    "Gothic Horror": {
        "CHAR_ROLES": ["vampire","occultist","nun","priest","monster hunter","ghost"],
        "CLOTHING": ["victorian dress","tailcoat","veil","leather gloves","fetters"],
        "PHYS_ATTR": ["pale skin","bloodshot eyes","gaunt","fangs"],
        "OBJECTS": ["candle","crucifix","silver dagger","coffin","grimoire"],
        "ENVIRONMENTS": ["ruined chapel","graveyard","crypt","foggy street","abandoned manor"],
        "TIME_OF_DAY": ["midnight","dusk"],
        "WEATHER": ["fog","rain","storm"],
        "LIGHTING": ["candlelight","moonlight","low key","hard shadows"],
        "COLORS": ["sepia","scarlet","ashen blue","black"],
        "CAMERA": ["dutch angle","close-up","high angle","long shot"],
        "COMPOSITION": ["heavy vignette","negative space","arched frames"],
        "MOOD": ["ominous","mournful","tense","macabre"],
        "STYLE": ["noir","painterly","cinematic"],
        "QUALITY": ["highly detailed","grain","dramatic shadows"],
        "EFFECTS": ["mist","motes","blood spatter"]
    },
    "Space Opera": {
        "CHAR_ROLES": ["pilot","admiral","smuggler","alien envoy","trooper","astromech"],
        "CLOTHING": ["flight suit","cape","armor plating","vac suit"],
        "PHYS_ATTR": ["glowing eyes","bioluminescent skin","horns","tendrils"],
        "OBJECTS": ["blaster","holomap","starfighter","hyperdrive core","laser sword"],
        "ENVIRONMENTS": ["starship bridge","hangar bay","desert planet","ice moon","asteroid base"],
        "TIME_OF_DAY": ["night","dawn"],
        "WEATHER": ["solar wind","dust storm","snow"],
        "LIGHTING": ["console glow","starlight","volumetric beams"],
        "COLORS": ["azure","violet","burnt orange","silver"],
        "CAMERA": ["wide shot","over-the-shoulder","top-down","low angle"],
        "COMPOSITION": ["rule of thirds","epic scale","foreground cockpit"],
        "MOOD": ["heroic","urgent","mysterious"],
        "STYLE": ["cinematic","anime","illustration"],
        "QUALITY": ["hdr","highly detailed","4k"],
        "EFFECTS": ["sparks","debris","engine trails","laser bolts"]
    },
    "Noir Detective": {
        "CHAR_ROLES": ["detective","femme fatale","mobster","cop","bartender"],
        "CLOTHING": ["trench coat","fedora","three-piece suit","evening gown","gloves"],
        "PHYS_ATTR": ["cigarette smoke","stubbled chin","shadowed eyes"],
        "OBJECTS": ["revolver","briefcase","whisky glass","matchbook","photograph"],
        "ENVIRONMENTS": ["rainy street","jazz club","motel room","police station","office with blinds"],
        "TIME_OF_DAY": ["night","late evening"],
        "WEATHER": ["rain","fog"],
        "LIGHTING": ["venetian blind light","low key","hard contrast","neon sign"],
        "COLORS": ["monochrome","sepia","scarlet accent"],
        "CAMERA": ["close-up","low angle","over-the-shoulder"],
        "COMPOSITION": ["silhouette","strong diagonals","negative space"],
        "MOOD": ["noir","tense","melancholic"],
        "STYLE": ["black and white","cinematic","pulp illustration"],
        "QUALITY": ["grain","high contrast","sharp focus"],
        "EFFECTS": ["rain droplets","cigarette smoke"]
    },
    "Modern Romance / Slice of Life": {
        "CHAR_ROLES": ["student","teacher","office worker","musician","photographer"],
        "CLOTHING": ["hoodie","sundress","school uniform","suit and tie","denim jacket"],
        "PHYS_ATTR": ["smiling eyes","rosy cheeks"],
        "OBJECTS": ["smartphone","coffee cup","bouquet","guitar","notebook"],
        "ENVIRONMENTS": ["café","apartment balcony","park bench","train station","beach at sunset"],
        "TIME_OF_DAY": ["golden hour","evening","morning"],
        "WEATHER": ["clear","drizzle"],
        "LIGHTING": ["warm lamp glow","soft daylight","neon reflections"],
        "COLORS": ["pastel","warm tones"],
        "CAMERA": ["portrait","close-up","mid-shot"],
        "COMPOSITION": ["rule of thirds","foreground bokeh"],
        "MOOD": ["warm","tender","nostalgic","bittersweet"],
        "STYLE": ["illustration","cinematic","anime"],
        "QUALITY": ["sharp focus","soft grain"]
    },
    "Post-Apocalyptic Survival": {
        "CHAR_ROLES": ["scavenger","wanderer","raider","survivor","mutant"],
        "CLOTHING": ["gas mask","patched leather","tattered cloak","survival gear"],
        "PHYS_ATTR": ["scarred","gaunt"],
        "OBJECTS": ["crossbow","makeshift weapon","rusty car","canned food","broken radio"],
        "ENVIRONMENTS": ["ruined city","desert wasteland","abandoned mall","collapsed highway","underground bunker"],
        "TIME_OF_DAY": ["noon","sunset"],
        "WEATHER": ["dust storm","smog","dry heat"],
        "LIGHTING": ["harsh sunlight","flickering torch","smoke haze"],
        "COLORS": ["desaturated","rust tones"],
        "CAMERA": ["wide shot","low angle"],
        "COMPOSITION": ["lonely silhouette","vast negative space"],
        "MOOD": ["grim","hopeless","desperate","tense"],
        "STYLE": ["cinematic","realistic"],
        "QUALITY": ["grain","highly detailed"]
    },
    "Mythic Africa": {
        "CHAR_ROLES": ["griot","warrior queen","rain shaman","hunter","ancestor spirit"],
        "CLOTHING": ["kente cloth","beadwork","ceremonial masks","painted skin"],
        "PHYS_ATTR": ["scarification patterns"],
        "OBJECTS": ["drum","spear","calabash","ritual staff","amulet"],
        "ENVIRONMENTS": ["savannah","baobab grove","sacred river","desert dunes","ancestral shrine"],
        "TIME_OF_DAY": ["blazing noon","moonlit night"],
        "WEATHER": ["dust wind","rainstorm"],
        "LIGHTING": ["firelight","moonlit ritual glow"],
        "COLORS": ["earthy palette","bold patterns"],
        "CAMERA": ["establishing shot","low angle"],
        "COMPOSITION": ["ceremonial procession","framed by trees"],
        "MOOD": ["spiritual","majestic","solemn","powerful"],
        "STYLE": ["painterly","cinematic"],
        "QUALITY": ["highly detailed"]
    },
    "Arabian Nights Fantasy": {
        "CHAR_ROLES": ["sultan","desert thief","genie","merchant","caravan guard"],
        "CLOTHING": ["turbans","flowing robes","veils","gold jewelry","sandals"],
        "PHYS_ATTR": ["kohl-lined eyes"],
        "OBJECTS": ["magic lamp","scimitar","flying carpet","spice jar","treasure chest"],
        "ENVIRONMENTS": ["desert oasis","palace hall","bazaar","caravan camp","hidden cave"],
        "TIME_OF_DAY": ["starlit night","golden sunset"],
        "WEATHER": ["hot wind","clear sky"],
        "LIGHTING": ["torchlight","golden glow","starlight"],
        "COLORS": ["saffron","turquoise","gold"],
        "CAMERA": ["wide shot","low angle"],
        "COMPOSITION": ["arched frames","flowing drapery"],
        "MOOD": ["exotic","mysterious","enchanting","adventurous"],
        "STYLE": ["painterly","cinematic","anime"],
        "QUALITY": ["highly detailed"]
    },
    "Far East Mythology": {
        "CHAR_ROLES": ["samurai","onmyoji","yokai","dragon spirit","shrine maiden"],
        "CLOTHING": ["kimono","hakama","straw hat","bamboo armor"],
        "PHYS_ATTR": ["fox ears","horns"],
        "OBJECTS": ["katana","ofuda scroll","torii gate","shrine lantern","folding fan"],
        "ENVIRONMENTS": ["bamboo forest","mountain shrine","misty lake","torii pathway","ancient village"],
        "TIME_OF_DAY": ["misty dawn","moonlit night"],
        "WEATHER": ["fog","snow"],
        "LIGHTING": ["lantern glow","moonlight"],
        "COLORS": ["indigo","vermillion","gold"],
        "CAMERA": ["three-quarter view","low angle"],
        "COMPOSITION": ["framed by torii","foreground reeds"],
        "MOOD": ["serene","spiritual","mystical","foreboding"],
        "STYLE": ["ink","painterly","anime"],
        "QUALITY": ["crisp lines","highly detailed"]
    },
    "Prehistoric Adventure": {
        "CHAR_ROLES": ["hunter-gatherer","tribal elder","cave child","shaman"],
        "CLOTHING": ["furs","bones","animal hides","painted skin"],
        "PHYS_ATTR": ["war paint"],
        "OBJECTS": ["stone spear","fire torch","drum","flint knife"],
        "ENVIRONMENTS": ["cave","volcanic plain","mammoth herd","river crossing","dense jungle"],
        "TIME_OF_DAY": ["dawn","twilight"],
        "WEATHER": ["ash fall","rain"],
        "LIGHTING": ["firelight","volcanic glow","dawn mist"],
        "COLORS": ["ochre","charcoal","earth tones"],
        "CAMERA": ["wide shot","low angle"],
        "COMPOSITION": ["petroglyph backdrop","smoke-filled air"],
        "MOOD": ["primal","dangerous","awe-inspiring"],
        "STYLE": ["painterly","cinematic"],
        "QUALITY": ["textured brushwork","highly detailed"]
    },
    "Western Frontier": {
        "CHAR_ROLES": ["cowboy","sheriff","outlaw","rancher","gambler"],
        "CLOTHING": ["wide-brimmed hat","poncho","spurs","leather vest","bandana"],
        "PHYS_ATTR": ["stubbled jaw"],
        "OBJECTS": ["revolver","lasso","whiskey bottle","deck of cards","saddle"],
        "ENVIRONMENTS": ["dusty town","saloon","desert canyon","train station","ranch"],
        "TIME_OF_DAY": ["blazing noon","sunset silhouette"],
        "WEATHER": ["dust wind","clear sky"],
        "LIGHTING": ["harsh sun","lantern glow"],
        "COLORS": ["sepia","sun-bleached tones"],
        "CAMERA": ["cowboy shot","wide shot","low angle"],
        "COMPOSITION": ["long shadow","doorway framing"],
        "MOOD": ["gritty","tense","adventurous","lawless"],
        "STYLE": ["cinematic","pulp illustration"],
        "QUALITY": ["grain","highly detailed"]
    }
}

# -----------------------------
# UI
# -----------------------------
st.subheader("1) Input")
colA, colB = st.columns([2,1])
with colA:
    detailed = st.text_area("Paste your detailed scene description (master prompt)", height=240, placeholder="Paste full cinematic scene here...")
with colB:
    char_name = st.text_input("Main character (optional)", placeholder="e.g., Alaric")
    char_sheet = st.text_area("Character sheet traits (optional)", height=100, placeholder="tall, lean, messy silver hair, sharp eyes, tattered coat")
    negative = st.text_area("Negative prompt (optional)", height=100, placeholder="e.g., blurry, low-res, extra fingers, deformed hands")

st.subheader("2) Options")
pack = st.selectbox("Story pack", list(STORY_PACKS.keys()), index=0)

col1, col2, col3 = st.columns(3)
with col1:
    style_choice = st.selectbox("Style preset", list(STYLE_PRESETS.keys()), index=0)
with col2:
    brevity = st.radio("Brevity", ["concise", "standard", "verbose"], index=1, horizontal=True)
with col3:
    use_labels = st.checkbox("Show section labels", value=True)

max_items = st.slider("Max terms per section", min_value=0, max_value=20, value=10, help="0 = unlimited")

with st.expander("Add a custom Story Pack (optional)"):
    st.write("Upload a JSON file or paste JSON defining extra vocabulary. It will merge on top of the selected pack.")
    up = st.file_uploader("Upload JSON", type=["json"], accept_multiple_files=False)
    pasted = st.text_area("Or paste JSON here", height=140, placeholder='{"OBJECTS": ["new prop"], "ENVIRONMENTS": ["new place"]}')
    custom_pack = {}
    if up is not None:
        try:
            custom_pack = json.load(up)
            st.success("Custom pack loaded from file.")
        except Exception as e:
            st.error(f"Failed to parse uploaded JSON: {e}")
    elif pasted.strip():
        try:
            custom_pack = json.loads(pasted)
            st.success("Custom pack parsed.")
        except Exception as e:
            st.error(f"Failed to parse pasted JSON: {e}")

# -----------------------------
# Generate
# -----------------------------
if st.button("Perfect my prompt ✨", type="primary"):
    text = detailed or ""

    # Merge selected story pack vocab (extend the sets)
    selected = STORY_PACKS.get(pack, {})
    def extend_set(base_set, key):
        for term in selected.get(key, []):
            base_set.add(term.lower())

    extend_set(CHAR_ROLES, "CHAR_ROLES")
    extend_set(CLOTHING, "CLOTHING")
    extend_set(PHYS_ATTR, "PHYS_ATTR")
    extend_set(OBJECTS, "OBJECTS")
    extend_set(ENVIRONMENTS, "ENVIRONMENTS")
    extend_set(TIME_OF_DAY, "TIME_OF_DAY")
    extend_set(WEATHER, "WEATHER")
    extend_set(LIGHTING, "LIGHTING")
    extend_set(COLORS, "COLORS")
    extend_set(CAMERA, "CAMERA")
    extend_set(COMPOSITION, "COMPOSITION")
    extend_set(MOOD, "MOOD")
    extend_set(STYLE, "STYLE")
    extend_set(QUALITY, "QUALITY")
    extend_set(EFFECTS, "EFFECTS")

    # Merge custom pack too
    if isinstance(custom_pack, dict) and custom_pack:
        def extend_with_custom(base_set, key):
            for term in custom_pack.get(key, []):
                base_set.add(str(term).lower())
        extend_with_custom(CHAR_ROLES, "CHAR_ROLES")
        extend_with_custom(CLOTHING, "CLOTHING")
        extend_with_custom(PHYS_ATTR, "PHYS_ATTR")
        extend_with_custom(OBJECTS, "OBJECTS")
        extend_with_custom(ENVIRONMENTS, "ENVIRONMENTS")
        extend_with_custom(TIME_OF_DAY, "TIME_OF_DAY")
        extend_with_custom(WEATHER, "WEATHER")
        extend_with_custom(LIGHTING, "LIGHTING")
        extend_with_custom(COLORS, "COLORS")
        extend_with_custom(CAMERA, "CAMERA")
        extend_with_custom(COMPOSITION, "COMPOSITION")
        extend_with_custom(MOOD, "MOOD")
        extend_with_custom(STYLE, "STYLE")
        extend_with_custom(QUALITY, "QUALITY")
        extend_with_custom(EFFECTS, "EFFECTS")

    # Extracted elements
    names = proper_names(text)
    if char_name and char_name not in names:
        names = [char_name] + names

    roles = find_terms(text, CHAR_ROLES)
    clothing = find_terms(text, CLOTHING)
    phys = find_terms(text, PHYS_ATTR)
    objs = find_terms(text, OBJECTS)
    envs = find_terms(text, ENVIRONMENTS)
    time = find_terms(text, TIME_OF_DAY)
    weather = find_terms(text, WEATHER)
    lighting = find_terms(text, LIGHTING)
    colors = find_terms(text, COLORS)
    camera = find_terms(text, CAMERA)
    comp = find_terms(text, COMPOSITION)
    mood = find_terms(text, MOOD)
    style = find_terms(text, STYLE)
    quality = find_terms(text, QUALITY)
    fx = find_terms(text, EFFECTS)

    # Compose sections
    char_bits = []
    if names:
        char_bits.append(", ".join(names[:2]))
    if roles:
        char_bits.append(", ".join(roles))
    if char_sheet:
        char_bits.append(char_sheet.strip())
    if phys:
        char_bits.append(", ".join(phys))
    if clothing:
        char_bits.append(", ".join(clothing))

    lighting_bits = []
    if colors:
        lighting_bits.append(", ".join(colors))
    if lighting:
        lighting_bits.append(", ".join(lighting))
    if time:
        lighting_bits.append(", ".join(time))
    if weather:
        lighting_bits.append(", ".join(weather))

    camera_bits = []
    if camera:
        camera_bits.append(", ".join(camera))
    if comp:
        camera_bits.append(", ".join(comp))

    style_bits = []
    preset_bits = STYLE_PRESETS.get(style_choice, [])
    if preset_bits:
        style_bits.extend(preset_bits)
    if style:
        style_bits.extend(style)
    if quality:
        style_bits.extend(quality)
    if fx:
        style_bits.extend(fx)

    sections = [
        ("Main Character", ", ".join([s for s in char_bits if s]) if char_bits else ""),
        ("Secondary / Objects", ", ".join(compress_list(objs, max_items))),
        ("Environment / Background", ", ".join(compress_list(envs, max_items))),
        ("Lighting & Color", ", ".join(compress_list(lighting_bits, max_items))),
        ("Camera & Composition", ", ".join(compress_list(camera_bits, max_items))),
        ("Mood / Emotion", ", ".join(compress_list(mood, max_items))),
        ("Style & Quality", ", ".join(compress_list(style_bits, max_items))),
    ]

    if negative:
        sections.append(("Negative", negative.strip()))

    kling_prompt = build_prompt(sections, mode=brevity, use_labels=use_labels)

    st.subheader("3) Kling-Ready Output")
    st.code(kling_prompt, language="text")
    st.download_button("Download prompt as .txt", data=kling_prompt, file_name="kling_prompt.txt", mime="text/plain")
    st.success("Done! Paste this into Kling. If results drift, reduce terms per section or switch to 'concise'.")

st.markdown("---")
st.caption("Pro tip: Keep your master prompt rich. Use this tool to translate it into short, tagged chunks Kling parses well.")
