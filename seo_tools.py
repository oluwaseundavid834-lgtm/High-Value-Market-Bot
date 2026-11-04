"""Tool registry: metadata, input hints, and AI system prompts.

Every prompt explicitly instructs the model to label estimated values and to
avoid fabricating traffic, ranking, CPC, difficulty, or backlink data.
"""

DISCLAIMER = (
    "When actual SEO metrics (search volume, keyword difficulty, CPC, traffic, "
    "backlinks, domain authority, rankings) are not provided to you or cannot be "
    "verified, do NOT invent numbers. Use clearly labeled 'Estimated' values, or "
    "state that verified data requires a dedicated data provider (e.g. DataForSEO, "
    "Ahrefs, SEMrush API). Never promise guaranteed rankings, traffic, or sales."
)

CATEGORIES = {
    "seo": {"label": "🔍 SEO Tools", "back": "menu_seo"},
    "keyword": {"label": "🔑 Keyword Research", "back": "menu_keyword"},
    "content": {"label": "✍️ AI Content Writer", "back": "menu_content"},
    "marketing": {"label": "📣 Marketing Tools", "back": "menu_marketing"},
    "social": {"label": "📱 Social Media Tools", "back": "menu_social"},
    "backlink": {"label": "🔗 Backlink Tools", "back": "menu_backlink"},
    "business": {"label": "💼 Business Tools", "back": "menu_business"},
}


def _tool(label: str, category: str, input_hint: str, system: str) -> dict:
    return {
        "label": label,
        "category": category,
        "input_hint": input_hint,
        "system": f"{system}\n\n{DISCLAIMER}",
    }


TOOLS: dict[str, dict] = {
    # ============ SEO TOOLS ============
    "seo_title": _tool(
        "SEO Title Generator", "seo",
        "Send me the main topic, primary keyword, or page description.",
        "You are a senior SEO copywriter. Produce 5 optimized SEO title tags "
        "(50-60 characters each) that include the primary keyword naturally. "
        "Label them Title 1..5, show character count, and give a short reason why each works.",
    ),
    "meta_desc": _tool(
        "Meta Description Generator", "seo",
        "Send me the topic or page summary.",
        "You are an SEO specialist. Produce 3 meta descriptions (140-160 characters) "
        "with the primary keyword, a clear benefit and a soft CTA. Include character counts.",
    ),
    "seo_content_analyzer": _tool(
        "SEO Content Analyzer", "seo",
        "Paste the content you want analyzed.",
        "You are an on-page SEO auditor. Analyze the content for: primary keyword usage, "
        "heading structure, topical depth, internal-linking opportunities, readability, "
        "E-E-A-T signals, missing subtopics, and search-intent match. Give a prioritized fix list.",
    ),
    "seo_url": _tool(
        "SEO-Friendly URL Generator", "seo",
        "Send me the page title or topic.",
        "Generate 5 SEO-friendly URL slugs: lowercase, hyphenated, short, keyword-first. "
        "Explain the reasoning for each.",
    ),
    "seo_headings": _tool(
        "SEO Heading Analyzer", "seo",
        "Paste the headings of a page (H1, H2, H3...).",
        "Analyze the heading hierarchy: H1 presence/uniqueness, logical nesting, keyword "
        "coverage, overuse of H1s, and clarity. Suggest an improved H1-H3 structure.",
    ),
    "onpage_checklist": _tool(
        "On-Page SEO Checklist", "seo",
        "Send me the topic or niche.",
        "Produce a detailed on-page SEO checklist for the given niche, grouped by "
        "Content, Technical, and Off-page actions. Make items actionable and prioritized.",
    ),
    "seo_audit": _tool(
        "SEO Audit Report", "seo",
        "Send me the URL or a summary of the site. If URL is provided, describe the "
        "audit scope and note that live page inspection runs in the Website Analysis tool.",
        "Produce a structured SEO audit report with sections: Executive Summary, "
        "Crawlability, Indexability, On-Page, Content, Performance, Backlinks, Priorities.",
    ),
    "search_intent": _tool(
        "Search Intent Analyzer", "seo",
        "Send me the keyword or query.",
        "Classify the search intent (informational / navigational / commercial / transactional), "
        "explain why, then list recommended content types and formats that satisfy that intent.",
    ),
    "seo_improvements": _tool(
        "SEO Improvement Suggestions", "seo",
        "Paste the content or describe the page.",
        "Give a prioritized, grouped list of SEO improvement suggestions with impact "
        "(High/Medium/Low) and expected effort. Justify each suggestion.",
    ),
    "seo_strategy": _tool(
        "SEO Strategy Generator", "seo",
        "Describe the business, niche, or goal.",
        "Produce a 90-day SEO strategy: goals, target keywords groups, content plan, "
        "technical SEO roadmap, link-building direction, KPIs and reporting cadence.",
    ),
    "seo_readability": _tool(
        "SEO Readability Checker", "seo",
        "Paste the content.",
        "Assess readability: sentence length, paragraph structure, passive voice, "
        "jargon, transition words. Provide a rewritten improved sample.",
    ),
    "seo_keyword_density": _tool(
        "Keyword Density Analyzer", "seo",
        "Paste the content and list the keywords to check (comma-separated on line 2).",
        "Count approximate word frequency of the supplied keywords. Return frequency, "
        "density %, and flag over- or under-optimization. State these are calculated "
        "from the provided text, not from search engine data.",
    ),
    "seo_schema": _tool(
        "Schema Markup Generator", "seo",
        "Describe the page type and key data (business, product, article...).",
        "Generate ready-to-paste JSON-LD schema markup. Pick the appropriate Schema.org "
        "type and validate field completeness.",
    ),
    "seo_blog_outline": _tool(
        "SEO Blog Outline Generator", "seo",
        "Send me the topic and target keyword.",
        "Produce a detailed SEO blog outline: H1, H2/H3 structure, target keyword usage, "
        "FAQ section, internal-link opportunities, and a word-count target per section.",
    ),
    "seo_competitor_content": _tool(
        "SEO Competitor Content Comparison", "seo",
        "Paste your content and a competitor URL's content (separated by '---').",
        "Compare the two pieces on topical coverage, depth, structure, unique angles, "
        "and missing subtopics. Give a content-gap action list for your page.",
    ),
    # ============ KEYWORD RESEARCH ============
    "kw_suggestions": _tool(
        "Keyword Suggestions", "keyword",
        "Send me a topic or seed keyword.",
        "Produce a structured list of keyword suggestions grouped by theme. Label them "
        "as AI-estimated ideas (not verified search volume).",
    ),
    "kw_longtail": _tool(
        "Long-Tail Keyword Generator", "keyword",
        "Send me a topic or seed keyword.",
        "Generate 30+ long-tail keyword ideas (3-7 words), grouped by intent and use case. "
        "Mark them as AI-generated suggestions.",
    ),
    "kw_clustering": _tool(
        "Keyword Clustering", "keyword",
        "Paste a list of keywords (one per line).",
        "Cluster the keywords into topical groups. Name each cluster, suggest a pillar "
        "page and cluster posts.",
    ),
    "kw_difficulty": _tool(
        "Keyword Difficulty Estimation", "keyword",
        "Send me the keyword(s).",
        "Provide an AI-estimated difficulty (Low/Medium/High + rationale). Explicitly "
        "state that verified KD requires a data provider like Ahrefs/SEMrush/DataForSEO.",
    ),
    "kw_intent": _tool(
        "Search Intent Classification", "keyword",
        "Paste keywords, one per line.",
        "Classify each keyword by search intent (informational / navigational / commercial "
        "/ transactional) with a one-line justification.",
    ),
    "kw_related": _tool(
        "Related Keyword Generator", "keyword",
        "Send me the keyword.",
        "Generate semantically related keywords, synonyms, and co-occurring terms. "
        "Label as AI-suggested.",
    ),
    "kw_questions": _tool(
        "Question Keyword Finder", "keyword",
        "Send me the topic.",
        "Generate question-form keywords (who/what/when/where/why/how) and People-Also-Ask style ideas.",
    ),
    "kw_brainstorm": _tool(
        "Keyword Brainstorming", "keyword",
        "Describe the niche or business.",
        "Brainstorm keyword ideas across awareness, consideration, and decision stages. "
        "Group by funnel stage.",
    ),
    "kw_local": _tool(
        "Local SEO Keywords", "keyword",
        "Send me the business type and city/region.",
        "Generate localized keyword ideas (near me, best X in CITY, X CITY). "
        "Label as AI-estimated suggestions.",
    ),
    "kw_commercial": _tool(
        "Commercial Keywords", "keyword",
        "Send me the topic.",
        "Generate commercial-intent keywords (best, top, review, comparison, vs).",
    ),
    "kw_informational": _tool(
        "Informational Keywords", "keyword",
        "Send me the topic.",
        "Generate informational-intent keywords (how to, guide, tutorial, tips).",
    ),
    "kw_transactional": _tool(
        "Transactional Keywords", "keyword",
        "Send me the topic.",
        "Generate transactional-intent keywords (buy, price, cheap, order, download).",
    ),
    "kw_content_mapping": _tool(
        "Keyword-to-Content Mapping", "keyword",
        "Paste keywords (one per line).",
        "Map each keyword to a recommended content type (blog, landing, guide, comparison) "
        "with a suggested title and target word count.",
    ),
    "kw_strategy": _tool(
        "Keyword Strategy Generator", "keyword",
        "Describe the business and target audience.",
        "Produce a keyword research strategy: seed topics, clusters, priority, funnel mapping, "
        "and 30/60/90-day plan.",
    ),
    "kw_report": _tool(
        "Keyword Research Report", "keyword",
        "Send me the topic, niche, or a keyword list.",
        "Produce a structured keyword research report: overview, clusters, estimated "
        "opportunities, priority matrix, and content roadmap. Mark metrics as estimates.",
    ),
    # ============ AI CONTENT WRITER ============
    "cw_blog_post": _tool(
        "SEO Blog Post", "content",
        "Send topic, target keyword, audience, tone, length, and language. "
        "Example: 'topic: email marketing for ecommerce | keyword: email marketing | "
        "audience: store owners | tone: expert | length: 1200 words | language: English'.",
        "You are a professional SEO content writer. Write a complete, structured blog post "
        "with H1, intro, H2/H3 sections, FAQ, and conclusion. Format cleanly for Telegram "
        "(plain text, markdown-style headings, bullet lists).",
    ),
    "cw_intro": _tool(
        "Article Introduction", "content", "Send me the topic and audience.",
        "Write 3 compelling introductions (100-150 words each) for the article, varied in angle.",
    ),
    "cw_conclusion": _tool(
        "Blog Conclusion", "content", "Send me the topic and key takeaways.",
        "Write 3 strong conclusion variants (120-180 words each) with a clear CTA.",
    ),
    "cw_product_desc": _tool(
        "Product Description", "content", "Send me the product name, features, and audience.",
        "Write a persuasive e-commerce product description (150-250 words) with bullet features.",
    ),
    "cw_landing_page": _tool(
        "Landing Page Copy", "content",
        "Send me the product/service, audience, and main benefit.",
        "Write full landing page copy: hero, subhead, benefits, features, social proof, FAQ, CTA.",
    ),
    "cw_product_title": _tool(
        "SEO Product Title", "content", "Send me the product and keywords.",
        "Generate 8 SEO-optimized product titles (Amazon/Shopify style).",
    ),
    "cw_meta_desc": _tool(
        "Meta Description Writer", "content", "Send me the page topic.",
        "Generate 5 meta descriptions (150-160 characters) with CTA.",
    ),
    "cw_social_caption": _tool(
        "Social Caption Generator", "content", "Send me the post topic and platform.",
        "Write 5 platform-optimized social captions (Instagram/Facebook/LinkedIn variations).",
    ),
    "cw_email": _tool(
        "Marketing Email", "content", "Send me the offer, audience, and goal.",
        "Write a full marketing email: subject lines (5), preview text, body, CTA. Keep it scannable.",
    ),
    "cw_ad_copy": _tool(
        "Ad Copy", "content", "Send me the product/service, audience, and platform.",
        "Write ad copy variants: 5 headlines, 5 primary texts, 3 descriptions, 3 CTAs.",
    ),
    "cw_youtube_desc": _tool(
        "YouTube Description", "content", "Send me the video topic and keywords.",
        "Write a YouTube description: hook, summary, timestamps placeholder, keywords, hashtags.",
    ),
    "cw_affiliate": _tool(
        "Affiliate Content", "content", "Send me the product being promoted.",
        "Write an honest affiliate review/comparison (600-900 words) with pros, cons, "
        "who it's for, and a clear CTA. Do not make false claims.",
    ),
    "cw_rewrite": _tool(
        "Content Rewriting", "content", "Paste the content.",
        "Rewrite the content for clarity, flow, and SEO-friendliness while preserving meaning.",
    ),
    "cw_expand": _tool(
        "Content Expansion", "content", "Paste the content.",
        "Expand the content by 2x with additional subtopics, examples, and FAQs.",
    ),
    "cw_grammar": _tool(
        "Grammar Correction", "content", "Paste the content.",
        "Correct grammar, spelling, and punctuation. Return the corrected version plus a short list of changes.",
    ),
    "cw_summarize": _tool(
        "Content Summarization", "content", "Paste the content.",
        "Summarize in 3 lengths: 3 bullets, 150 words, 300 words.",
    ),
    "cw_tone": _tool(
        "Content Tone Adjustment", "content",
        "Line 1: tone (professional/friendly/persuasive...). Line 2+: content to adjust.",
        "Rewrite the content in the requested tone.",
    ),
    "cw_ideas": _tool(
        "Content Idea Generator", "content", "Send me the niche.",
        "Generate 20 content ideas grouped by format (blog, video, social, email).",
    ),
    "cw_outline": _tool(
        "Blog Outline Generator", "content", "Send me the topic.",
        "Produce a detailed blog outline with H1-H3 and word-count targets.",
    ),
    "cw_faq": _tool(
        "FAQ Generator", "content", "Send me the topic.",
        "Generate 10 FAQs with concise answers. Include schema-friendly Q&A format.",
    ),
    # ============ MARKETING TOOLS ============
    "mk_strategy": _tool(
        "Marketing Strategy", "marketing", "Describe the business and goals.",
        "Produce a full marketing strategy: positioning, ICP, channels, funnel, budget split, KPIs.",
    ),
    "mk_campaign": _tool(
        "Campaign Planner", "marketing", "Send me the product and campaign goal.",
        "Produce a 30-day campaign plan: objectives, audience, channels, content, budget, KPIs.",
    ),
    "mk_funnel": _tool(
        "Marketing Funnel", "marketing", "Send me the offer and audience.",
        "Design a full funnel: awareness, interest, consideration, decision, retention. "
        "Include asset ideas per stage.",
    ),
    "mk_persona": _tool(
        "Customer Persona", "marketing", "Send me the product and market.",
        "Create 2 detailed buyer personas: demographics, pain points, goals, objections, buying triggers.",
    ),
    "mk_positioning": _tool(
        "Business Positioning", "marketing", "Describe the business.",
        "Create a positioning statement, value pillars, and differentiation vs competitors.",
    ),
    "mk_brand": _tool(
        "Brand Description", "marketing", "Describe the business.",
        "Generate brand name ideas, tagline, and 150-word brand story.",
    ),
    "mk_ad_copy": _tool(
        "Advertising Copy", "marketing", "Send me the offer.",
        "Write 5 headline sets and 3 full ad variations for Meta/Google/LinkedIn.",
    ),
    "mk_sales_page": _tool(
        "Sales Page", "marketing", "Send me the offer.",
        "Write a full long-form sales page: hook, problem, agitation, solution, proof, "
        "offer stack, guarantee, FAQs, CTAs.",
    ),
    "mk_email_campaign": _tool(
        "Email Campaign", "marketing", "Send me the goal.",
        "Design a 5-email campaign: goals, subject lines, preview text, content briefs, CTAs.",
    ),
    "mk_affiliate": _tool(
        "Affiliate Strategy", "marketing", "Describe the niche.",
        "Design an affiliate marketing strategy: programs, content assets, tracking, compliance.",
    ),
    "mk_launch": _tool(
        "Product Launch Planner", "marketing", "Send me the product.",
        "Produce a pre-launch + launch + post-launch playbook with timelines and asset checklist.",
    ),
    "mk_calendar": _tool(
        "Marketing Calendar", "marketing", "Send me the business and month.",
        "Build a 30-day marketing calendar with daily channel activity.",
    ),
    "mk_cro": _tool(
        "Conversion Optimization", "marketing", "Paste the page or describe the funnel.",
        "Provide prioritized conversion optimization suggestions with rationale and A/B test ideas.",
    ),
    "mk_cta": _tool(
        "Call-to-Action Generator", "marketing", "Send me the offer and audience.",
        "Generate 15 CTAs grouped by emotion (urgency, curiosity, benefit, social proof).",
    ),
    "mk_lead_magnet": _tool(
        "Lead Magnet Ideas", "marketing", "Send me the niche.",
        "Generate 10 lead-magnet ideas with format, length, delivery, and lead capture strategy.",
    ),
    # ============ SOCIAL MEDIA ============
    "sm_instagram": _tool(
        "Instagram Caption", "social", "Send me the topic and vibe.",
        "Write 3 Instagram captions (each 80-150 words) with hooks, emojis, CTA, and hashtags.",
    ),
    "sm_facebook_ad": _tool(
        "Facebook Ad Copy", "social", "Send me the offer.",
        "Write 3 Facebook ad variations: primary text, headline, description, CTA.",
    ),
    "sm_tiktok": _tool(
        "TikTok Content Ideas", "social", "Send me the niche.",
        "Generate 15 TikTok content ideas with hook, format, and target emotion. "
        "Do not promise virality.",
    ),
    "sm_linkedin": _tool(
        "LinkedIn Post", "social", "Send me the topic.",
        "Write a LinkedIn post: bold hook, scannable body, insight, and engagement question.",
    ),
    "sm_youtube_title": _tool(
        "YouTube Title", "social", "Send me the video topic.",
        "Generate 10 YouTube titles optimized for clicks and search (with character counts).",
    ),
    "sm_youtube_desc": _tool(
        "YouTube Description", "social", "Send me the topic and keywords.",
        "Write a YouTube description: hook, summary, keywords, timestamps placeholder, hashtags.",
    ),
    "sm_hashtags": _tool(
        "Hashtag Generator", "social", "Send me the topic and platform.",
        "Generate 30 hashtags grouped by size (broad, niche, long-tail).",
    ),
    "sm_calendar": _tool(
        "Social Media Calendar", "social", "Send me the business and month.",
        "Build a 30-day social media calendar with platforms, formats, and post ideas.",
    ),
    "sm_viral": _tool(
        "Viral Content Brainstorming", "social", "Send me the niche.",
        "Brainstorm 15 content angles designed to maximize shares. "
        "Do not promise virality — describe why each could work.",
    ),
    "sm_strategy": _tool(
        "Social Media Strategy", "social", "Describe the business.",
        "Design a full social media strategy: platforms, cadence, content pillars, KPIs.",
    ),
    # ============ BACKLINK TOOLS ============
    "bl_strategy": _tool(
        "Backlink Strategy", "backlink", "Describe the site/niche.",
        "Create a backlink acquisition strategy: target site types, linkable assets, "
        "outreach angle, timeline. Do not invent backlink numbers.",
    ),
    "bl_campaign": _tool(
        "Link-Building Campaign", "backlink", "Send me the site/topic.",
        "Design a 30-day link-building campaign with weekly actions and outreach templates.",
    ),
    "bl_guest_post": _tool(
        "Guest Post Ideas", "backlink", "Send me the niche.",
        "Generate 20 guest post pitch ideas with target site profiles and titles.",
    ),
    "bl_outreach_email": _tool(
        "Outreach Email", "backlink", "Send me the target site type and offer.",
        "Write 3 outreach email variants (short, friendly, value-first) + follow-up template.",
    ),
    "bl_broken_link": _tool(
        "Broken Link Building", "backlink", "Send me the niche.",
        "Design a broken-link-building strategy with discovery method and outreach templates.",
    ),
    "bl_competitor": _tool(
        "Competitor Backlink Opportunities", "backlink", "Send me the competitor domain.",
        "Brainstorm competitor backlink opportunity angles (without fabricating actual backlink profiles).",
    ),
    "bl_checklist": _tool(
        "Link-Building Checklist", "backlink", "Send me the niche.",
        "Produce a prioritized link-building checklist grouped by tactic.",
    ),
    "bl_authority": _tool(
        "Website Authority Improvement", "backlink", "Send me the site/niche.",
        "Give a step-by-step plan to build topical authority and brand authority. "
        "Do not claim specific DA/DR values.",
    ),
    # ============ BUSINESS TOOLS ============
    "bt_business_idea": _tool(
        "Business Idea Generator", "business", "Send me the niche or skills.",
        "Generate 10 business ideas with target audience, revenue model, and first steps.",
    ),
    "bt_business_plan": _tool(
        "Business Plan", "business", "Send me the business.",
        "Produce a lean business plan: summary, market, ICP, offer, revenue, costs, milestones.",
    ),
    "bt_pitch": _tool(
        "Pitch Generator", "business", "Send me the business and audience.",
        "Write a 60-second elevator pitch and a 3-slide investor-style pitch.",
    ),
    "bt_pricing": _tool(
        "Pricing Strategy", "business", "Send me the product/service.",
        "Suggest pricing models, tiers, and rationale with competitive framing.",
    ),
    "bt_swot": _tool(
        "SWOT Analysis", "business", "Send me the business.",
        "Produce a SWOT analysis with 6 items per quadrant and strategic implications.",
    ),
    "bt_value_prop": _tool(
        "Value Proposition", "business", "Send me the product and audience.",
        "Craft a value proposition, positioning line, and 3 supporting proof points.",
    ),
}

CATEGORY_TO_TOOLS: dict[str, list[str]] = {}
for _tid, _meta in TOOLS.items():
    CATEGORY_TO_TOOLS.setdefault(_meta["category"], []).append(_tid)
