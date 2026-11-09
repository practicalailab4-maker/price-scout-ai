
const button = document.getElementById("research-btn");
const activity = document.getElementById("activity");
const results = document.getElementById("results");
const productInput = document.getElementById("product");

let priceChart = null;
let verificationChart = null;
let signalChart = null;
let relatedChart = null;

function numberToAtlasWords(number) {
    const ones = [
        "zero", "one", "two", "three", "four", "five",
        "six", "seven", "eight", "nine", "ten",
        "eleven", "twelve", "thirteen", "fourteen",
        "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"
    ];

    const tens = [
        "", "", "twenty", "thirty", "forty",
        "fifty", "sixty", "seventy", "eighty", "ninety"
    ];

    function underThousand(n) {
        if (n < 20) return ones[n];
        if (n < 100) {
            return tens[Math.floor(n / 10)] +
                (n % 10 ? "-" + ones[n % 10] : "");
        }

        return ones[Math.floor(n / 100)] + " hundred" +
            (n % 100 ? " " + underThousand(n % 100) : "");
    }

    if (!Number.isSafeInteger(number) || number < 0) {
        return String(number);
    }

    if (number < 1000) return underThousand(number);

    if (number < 1000000) {
        return underThousand(Math.floor(number / 1000)) +
            " thousand" +
            (number % 1000
                ? " " + underThousand(number % 1000)
                : "");
    }

    return String(number);
}
function prepareAtlasNarration(text) {
    return String(text)
        .replace(/\bLenovo\s+LOQ(\s+Essential)?\s+15\s*\(Gen\s*\d+\)/gi, (_, essential) =>
            `Lenovo LOQ${essential || ""}`
        )
        .replace(/\b(Intel\s+Core\s+i[3579])[\s\u2010-\u2015-]*\d{4,5}[A-Z]*\b/gi, "$1")
        .replace(/\bCPU\b/gi, "processor")
        .replace(/\biGPU\b/gi, "integrated graphics")
        .replace(/\bTDP\b/gi, "thermal design power")
        .replace(/\b(\d+)[\s\u00A0\u202F]*W\b/g, "$1 watts")
        .replace(/\b(\d+)[-\u2011\u2010\u2013]core\b/gi, "$1 core")
        .replace(/\bzero\b/gi, "oh")
        .replace(/\b(AMD\s+)?Ryzen\s+([3579])\s+\d{4,5}[A-Z0-9]*\b/gi, (_, brand, series) => `${brand || ""}Ryzen ${series}`)
        .replace(/\bIntel\s+Core\s+Ultra\s+([3579])\s+\d{3,5}[A-Z]*\b/gi, (_, series) => `Intel Core Ultra ${series}`)
        
        // Remove Markdown formatting.
        .replace(/\*\*/g, "")
        .replace(/#{1,6}\s/g, "")
        .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")

        // Read dollar amounts with cents naturally.
        .replace(/\$([\d,]+)\.(\d{2})\b/g, (_, dollars, cents) => {
            const amount = Number(dollars.replace(/,/g, ""));
            const centAmount = Number(cents);

            return `${numberToAtlasWords(amount)} dollars` +
                (centAmount > 0
                    ? ` and ${centAmount} cents`
                    : "");
        })

        // Read whole-dollar prices naturally.
        .replace(/\$([\d,]+)\b/g, (_, dollars) =>
            `${Number(dollars.replace(/,/g, "")).toLocaleString("en-US")} dollars`
        );
}
let atlasAudio = null;

async function speakResearchBriefing(text) {
    // Add ?mute=1 to the address to silence the spoken briefing (no audio, no ElevenLabs request).
    if (new URLSearchParams(location.search).has("mute")) return;

    // Stop any previous narration.
    window.speechSynthesis?.cancel();

    if (atlasAudio) {
        atlasAudio.pause();
        atlasAudio.src = "";
        atlasAudio = null;
    }

    try {
        const response = await fetch("/api/atlas/speak", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ text: prepareAtlasNarration(text) })
        });

        if (!response.ok) {
            throw new Error(`Atlas voice request failed: ${response.status}`);
        }

        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);

        atlasAudio = new Audio(audioUrl);

        atlasAudio.addEventListener("ended", () => {
            URL.revokeObjectURL(audioUrl);
        }, { once: true });

        await atlasAudio.play();

    } catch (error) {
        console.error("Atlas narration error:", error);
    }
}


function makeElement(tag, text, className = "") {
    const element = document.createElement(tag);
    element.textContent = text;
    if (className) element.className = className;
    return element;
}

const researchStages = [
    "Product Analysis",
    "Retailer Research",
    "Product Comparison",
    "AI Insights"
];

function showResearchTimeline(activeStep) {
    activity.replaceChildren();

    const timeline = document.createElement("div");
    timeline.className = "ai-timeline";

    researchStages.forEach((stage, index) => {
        const item = document.createElement("div");

        item.className = "ai-timeline-step";

        if (index < activeStep) {
            item.classList.add("stage-complete");
        } else if (index === activeStep) {
            item.classList.add("stage-active");
        } else {
            item.classList.add("stage-pending");
        }


        const symbol = index < activeStep ? "✓" :
            index === activeStep ? "◉" : "○";

        item.textContent = `${symbol} ${stage}`;
        timeline.appendChild(item);
    });

    activity.appendChild(timeline);
}

const researchMessages = [
    "🔎 Analyzing product request...",
    "🧠 AI examining product specifications...",
    "🌐 Researching retailer information...",
    "📊 Preparing price comparisons...",
    "✨ Generating product insights..."
];

let researchAnimation = null;


function startResearchAnimation() {
    let step = 0;

    activity.classList.add("ai-working");
    showResearchTimeline(step);

    researchAnimation = setInterval(() => {
        step = (step + 1) % researchStages.length;
        showResearchTimeline(step);
    }, 1600);
}


function stopResearchAnimation() {
    activity.classList.remove("ai-working");
    if (researchAnimation !== null) {
        clearInterval(researchAnimation);
        researchAnimation = null;
    }
}

button.addEventListener("click", async () => {
    const product = productInput.value.trim();

    if (!product) {
        activity.textContent = "Please enter a product name.";
        return;
    }


    button.disabled = true;
    button.textContent = "Researching...";
    startResearchAnimation();
    results.replaceChildren();


    try {
        const response = await fetch("/api/research", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ product })
        });

        if (!response.ok) {
            throw new Error(`Research failed: ${response.status}`);
        }

        const payload = await response.json();
        const data = payload.research;

        if (!data || !Array.isArray(data.offers)) {
            throw new Error("Unexpected research response.");
        }

        showResearchTimeline(researchStages.length);
        renderDashboard(data);
        const validOffers = data.offers
            .filter(offer =>
                typeof offer.price === "number" &&
                Number.isFinite(offer.price) &&
                offer.price > 0
            )
            .sort((a, b) => a.price - b.price);

        const lowestOffer = validOffers[0];

        let briefing = [
            `Price Scout Intelligence. Your research on ${data.product || product} is complete.`,

            

            lowestOffer
                ? `The lowest reported price is ${new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(lowestOffer.price)}, offered by ${lowestOffer.retailer}.`
                : `No usable retailer prices were available.`,

            `Please note that these prices are AI-reported and have not been independently verified.`,

            data.recommendation
                ? `Our buying recommendation is: ${data.recommendation}`
                : `Review the retailer information carefully before making a purchase.`
        ].join(" ");
        const topThreeProducts = Array.isArray(data.related_products)
            ? data.related_products
                .filter(item =>
                    item &&
                    typeof item.name === "string" &&
                    typeof item.value_score === "number" &&
                    Number.isFinite(item.value_score)
                )
                .sort((a, b) => b.value_score - a.value_score)
                .slice(0, 3)
            : [];
        console.log("ATLAS RESEARCH DATA:", data.related_products);
        const businessAnalysis = topThreeProducts.map((item, index) => {
            const spokenName = /^Lenovo\s+LOQ\b/i.test(item.name)
                ? "Lenovo LOQ" + (/\bEssential\b/i.test(item.name) ? " Essential" : "")
                : item.name;
            console.log("ATLAS PRODUCT DETAILS:", item);
            const ranking = ["first", "second", "third"][index];

            const explanation =
                typeof item.score_reason === "string" && item.score_reason.trim()
                    ? item.score_reason.trim()
                    : "A detailed explanation was not included in this research.";

            return (
                `In ${ranking} place is ${spokenName}, ` +
                `with an AI value score of ${item.value_score} out of one hundred. ` +
                `${explanation} `
            );
        }).join(" ");

        briefing += " Now, let's examine why the top products scored differently. " +
            businessAnalysis;
        briefing += " Ultimately, the best purchasing decision balances performance, price, and long-term value. " +
            "Use these findings to guide your selection, and confirm current pricing and availability before making your final purchase. " +
            "The analysis provides a basis for comparing alternatives; however, final procurement approval should remain contingent upon verification of current pricing, product specifications, and supplier terms.";
        speakResearchBriefing(briefing);

    } catch (error) {
        console.error(error);
        activity.textContent =
            "Research failed. Check the server terminal for details.";
    

    } finally {
        stopResearchAnimation();
        button.disabled = false;
        button.textContent = "Research Product";
    }

});

function renderDashboard(data) {
    if (priceChart) priceChart.destroy();
    if (verificationChart) verificationChart.destroy();
    if (signalChart) signalChart.destroy();
    if (relatedChart) relatedChart.destroy();

    results.replaceChildren();

    results.appendChild(
        makeElement("h3", data.product || "Product Research")
    );


    const notice = document.createElement("div");
    notice.className = "ai-notice";

    const noticeIcon = makeElement("div", "✦", "ai-notice-icon");

    const noticeContent = document.createElement("div");
    noticeContent.append(
        makeElement(
            "strong",
            "AI-POWERED PRICE INTELLIGENCE"
        ),
        makeElement(
            "p",
            "Prices are AI-reported. Confirm the latest offer directly with the retailer before purchasing."
        )
    );

    notice.append(noticeIcon, noticeContent);
    results.appendChild(notice);


    // Validate prices before calculating statistics.
    const offers = data.offers.filter(
        offer =>
            typeof offer.price === "number" &&
            Number.isFinite(offer.price) &&
            offer.price > 0 &&
            typeof offer.retailer === "string"
    );

    const prices = offers.map(offer => offer.price);
    const lowest = prices.length ? Math.min(...prices) : null;
    const highest = prices.length ? Math.max(...prices) : null;
    const average = prices.length
        ? prices.reduce((a, b) => a + b, 0) / prices.length
        : null;

    // STAT CARDS
    const stats = document.createElement("div");
    stats.className = "stats-grid";

    const statValues = [
        ["Lowest Reported", lowest === null ? "N/A" : `$${lowest.toFixed(2)}`],
        ["Average Reported", average === null ? "N/A" : `$${average.toFixed(2)}`],
        ["Price Spread", lowest === null ? "N/A" : `$${(highest - lowest).toFixed(2)}`]
    ];

    for (const [label, value] of statValues) {
        const card = document.createElement("div");
        card.className = "stat-card";
        card.append(
            makeElement("div", value, "stat-value"),
            makeElement("div", label, "stat-label")
        );
        stats.appendChild(card);
    }

    results.appendChild(stats);

    // CHART CONTAINERS
    const charts = document.createElement("div");
    charts.className = "charts-grid";

    const barPanel = document.createElement("div");
    barPanel.className = "chart-panel";
    barPanel.appendChild(makeElement("h4", "Retailer Price Comparison"));


    const barCanvas = document.createElement("canvas");

    const barChartContainer = document.createElement("div");
    barChartContainer.className = "price-chart-container";

    barChartContainer.appendChild(barCanvas);
    barPanel.appendChild(barChartContainer);


    const donutPanel = document.createElement("div");
    donutPanel.className = "chart-panel";
    donutPanel.appendChild(makeElement("h4", "Source Verification"));


    const donutWrapper = document.createElement("div");
    donutWrapper.className = "donut-wrapper";

    const donutCanvas = document.createElement("canvas");

    const donutCenter = document.createElement("div");
    donutCenter.className = "donut-center";

    donutWrapper.append(donutCanvas, donutCenter);
    donutPanel.appendChild(donutWrapper);



    // AI SIGNAL CHART CONTAINER
    const signalPanel = document.createElement("div");
    signalPanel.className = "chart-panel signal-panel";

    signalPanel.appendChild(
        makeElement("h4", "AI Product Value Comparison")
    );

    signalPanel.appendChild(
        makeElement(
            "p",
            "AI-assessed value scores across comparable products — not a timeline or measured benchmark.",
            "signal-caption"
        )
    );

    const signalWrapper = document.createElement("div");
    signalWrapper.className = "ai-value-arena";

    const signalCanvas = document.createElement("canvas");
    signalCanvas.style.display = "none";

    signalWrapper.appendChild(signalCanvas);
    signalPanel.appendChild(signalWrapper);

    const arenaCards = document.createElement("div");
    arenaCards.style.display = "grid";
    arenaCards.style.gridTemplateColumns = "repeat(3, minmax(0, 1fr))";
    arenaCards.style.gap = "18px";
    arenaCards.style.padding = "20px 0";

    const topProducts = (Array.isArray(data.related_products)
        ? data.related_products
        : [])
        .filter(product =>
            product &&
            typeof product.name === "string" &&
            Number.isFinite(Number(product.value_score))
        )
        .sort((a, b) => Number(b.value_score) - Number(a.value_score))
        .slice(0, 3);

    const arenaColors = ["#78DCFF", "#FFD400", "#A78BFA"];

    topProducts.forEach((product, index) => {
        const score = Math.max(0, Math.min(100, Number(product.value_score)));
        const color = arenaColors[index];

        const card = document.createElement("div");
        card.style.cssText = `
        background: rgba(255,255,255,0.07);
        border: 1px solid rgba(255,255,255,0.16);
        border-radius: 22px;
        padding: 24px 12px;
        text-align: center;
        min-width: 0;
    `;

        const rank = document.createElement("div");
        rank.textContent = `RANK ${String(index + 1).padStart(2, "0")}`;
        rank.style.cssText = "color:#C9C3F5;letter-spacing:2px;font-size:12px;";

        const ring = document.createElement("div");
        ring.style.cssText = `
        width: 180px;
        height: 180px;
        max-width: 100%;
        margin: 20px auto;
        border-radius: 50%;
        background: conic-gradient(
            ${color} ${score}%,
            rgba(255,255,255,0.12) ${score}%
        );
        display: flex;
        align-items: center;
        justify-content: center;
    `;

        const center = document.createElement("div");
        center.style.cssText = `
        width: 78%;
        height: 78%;
        border-radius: 50%;
        background: #1a1052;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    `;

        const number = document.createElement("strong");
        number.textContent = Math.round(score);
        number.style.cssText = "font-size:48px;color:#FFFFFF;line-height:1;";

        const outOf = document.createElement("span");
        outOf.textContent = "/ 100";
        outOf.style.cssText = "font-size:18px;color:#C9C3F5;margin-top:8px;";

        center.append(number, outOf);
        ring.appendChild(center);

        const name = document.createElement("div");
        name.textContent = product.name;
        name.style.cssText = `
        color:#F1F5F9;
        font-size:14px;
        font-weight:600;
        overflow-wrap:anywhere;
    `;

        card.append(rank, ring, name);
        arenaCards.appendChild(card);
    });

    signalWrapper.appendChild(arenaCards);


    // RELATED PRODUCTS COMPARISON
    const relatedPanel = document.createElement("div");
    relatedPanel.className = "chart-panel related-panel";

    relatedPanel.appendChild(
        makeElement("h4", "AI Related Products Comparison")
    );

    relatedPanel.appendChild(
        makeElement(
            "p",
            "Comparable products and AI-assessed value scores",
            "signal-caption"
        )
    );

    const relatedWrapper = document.createElement("div");
    relatedWrapper.className = "related-chart-container";

    const relatedCanvas = document.createElement("canvas");
    relatedWrapper.appendChild(relatedCanvas);
    relatedPanel.appendChild(relatedWrapper);


    // Visible explanations for AI-assessed product scores
    const insightsPanel = document.createElement("div");
    insightsPanel.className = "chart-panel related-panel";

    insightsPanel.appendChild(
        makeElement("h4", "Why These Products Scored Differently")
    );

    const insightProducts = Array.isArray(data.related_products)
        ? data.related_products.slice(0, 8)
        : [];

    if (insightProducts.length) {
        insightProducts.forEach((product) => {
            if (!product || typeof product.name !== "string") return;

            const insight = document.createElement("div");
            insight.className = "product-value-insight";

            const score = Number(product.value_score);
            const scoreText = Number.isFinite(score)
                ? `${Math.max(0, Math.min(100, score))}/100`
                : "Not scored";

            insight.appendChild(
                makeElement("strong", `${product.name} — ${scoreText}`)
            );

            insight.appendChild(
                makeElement(
                    "p",
                    product.score_reason || "AI explanation not available."
                )
            );

            insightsPanel.appendChild(insight);
        });
    } else {
        insightsPanel.appendChild(
            makeElement("p", "No related-product insights available.")
        );
    }

    // PRODUCT INTELLIGENCE FLOW — SANKEY DIAGRAM
    const sankeyPanel = document.createElement("div");
    sankeyPanel.className = "chart-panel related-panel sankey-panel";

    sankeyPanel.appendChild(
        makeElement("h4", "How Do These Products Compare?")
    );

    sankeyPanel.appendChild(
        makeElement(
            "p",
            "BRAND → PRODUCT → SEGMENT → AI VALUE. Follow the ribbons from each manufacturer through individual products to their market segment and AI-assessed value. Wider ribbons represent more products — not higher prices or sales.",
            "signal-caption"
        )
    );

    const sankeyContainer = document.createElement("div");
    sankeyContainer.className = "sankey-container";

    
    // Prepare real comparable products for a four-stage Sankey
    const sankeyProducts = Array.isArray(data.related_products)
        ? data.related_products
            .filter(item =>
                item &&
                typeof item.name === "string" &&
                item.name.trim()
            )
            .slice(0, 15)
        : [];
    console.log(
        "Sankey comparable products:",
        sankeyProducts.length,
        sankeyProducts.map(product => product.name)
    );
    const sankeyNodes = [];
    const sankeyLinks = new Map();

    function addSankeyNode(id, label, stage) {
        if (!sankeyNodes.some(node => node.id === id)) {
            sankeyNodes.push({ id, label, stage });
        }
    }

    function addSankeyLink(source, target) {
        const key = JSON.stringify([source, target]);
        sankeyLinks.set(key, (sankeyLinks.get(key) || 0) + 3);
    }

    sankeyProducts.forEach(product => {
        const brand =
            typeof product.brand === "string" && product.brand.trim()
                ? product.brand.trim()
                : "Unknown brand";

        const productName = product.name.trim();

        const category =
            ["Budget", "Midrange", "Premium"].includes(product.category)
                ? product.category
                : "Unknown segment";

        const score = Number(product.value_score);

        const valueCategory =
            product.value_score == null || !Number.isFinite(score)
                ? "Unknown value"
                : score >= 85
                    ? "High value"
                    : score >= 70
                        ? "Balanced value"
                        : "Lower value";

        const brandId = `brand:${brand}`;
        const productId = `product:${productName}`;
        const segmentId = `segment:${category}`;
        const valueId = `value:${valueCategory}`;

        // Four stages:
        // Brand → Product → Segment → AI Value
        addSankeyNode(brandId, brand, 0);
        addSankeyNode(productId, productName, 1);
        addSankeyNode(segmentId, category, 2);
        addSankeyNode(valueId, valueCategory, 3);

        addSankeyLink(brandId, productId);
        addSankeyLink(productId, segmentId);
        addSankeyLink(segmentId, valueId);
        // Fifth stage: AI Value → Product Specifications
        const specs = product.key_specs;

        if (specs && typeof specs === "object" && !Array.isArray(specs)) {
            Object.entries(specs).forEach(([specName, specValue]) => {
                if (specValue == null || String(specValue).trim() === "") {
                    return;
                }

                const specLabel = `${specName}: ${specValue}`;
                const specId = `spec:${specLabel}`;

                addSankeyNode(specId, specLabel, 4);
                addSankeyLink(valueId, specId);
            });
        }
    });

    const sankeyData = {
        nodes: sankeyNodes,
        links: Array.from(sankeyLinks, ([key, value]) => {
            const [source, target] = JSON.parse(key);
            return { source, target, value };
        })
    };

    // Draw the Sankey flow diagram
    if (
        typeof d3 !== "undefined" &&
        typeof d3.sankey === "function" &&
        sankeyData.links.length > 0
    ) {
        const width = 1400;
        const height = 850;

        

        const svg = d3.select(sankeyContainer)
            .append("svg")
            .attr("viewBox", `0 0 ${width} ${height}`)
            .attr("role", "img")
            .attr("aria-label", "Product flow from brand to price segment to AI value category");

        const sankeyLayout = d3.sankey()
            .nodeId(node => node.id)
            .nodeWidth(16)
            .nodePadding(60)
            .nodeAlign(d3.sankeyJustify)
            .nodeSort((a, b) => {
                if (a.stage === 0 && b.stage === 0) {
                    return a.id.startsWith("brand:Intel") ? -1 : 1;
                }
                return 0;
            })
            .extent([[65, height * 0.08], [width - 75, height * 0.92]]);

        const graph = sankeyLayout({
            nodes: sankeyData.nodes.map(node => ({ ...node })),
            links: sankeyData.links.map(link => ({ ...link }))
        });

        // Calm palette: one soft hue per brand, muted gold for segments, quiet slate for the rest
        const brandHues = ["#7FB7D6", "#A99BD6", "#8FC9B8", "#C9A7C0"];
        const brandNodes = graph.nodes.filter(n => n.stage === 0);
        const brandColor = new Map(brandNodes.map((n, i) => [n.id, brandHues[i % brandHues.length]]));
        const colorByNode = new Map();
        graph.nodes.forEach(n => {
            if (n.stage === 0) colorByNode.set(n.id, brandColor.get(n.id));
        });
        graph.links.forEach(l => {
            if (l.source.stage === 0) colorByNode.set(l.target.id, brandColor.get(l.source.id));
        });
        graph.nodes.forEach(n => {
            if (!colorByNode.has(n.id)) colorByNode.set(n.id, n.stage === 2 ? "#CDBB85" : "#9AA3C7");
        });

        svg.append("g")
            .selectAll("path")
            .data(graph.links)
            .join("path")
            .attr("d", d3.sankeyLinkHorizontal())
            .attr("fill", "none")
            .attr("stroke", link => colorByNode.get(link.source.id))
            .attr("stroke-opacity", 0.32)
.attr("stroke-width", link => Math.max(3, link.width))
            .style("cursor", "pointer")
            .on("mouseenter", function () {
                d3.select(this)
                    .interrupt()
                    .raise()
                    .transition()
                    .duration(250)
                    .attr("stroke-opacity", 0.75);
            })
            .on("mouseleave", function () {
                d3.select(this)
                    .interrupt()
                    .transition()
                    .duration(350)
                    .attr("stroke-opacity", 0.32);
            })
            .append("title")

            .text(link =>
                `${link.source.label} → ${link.target.label}: ${link.value} product(s)`
            );

        const nodes = svg.append("g")
            .selectAll("g")
            .data(graph.nodes)
            .join("g");

        nodes.append("rect")
            .attr("x", node => node.x0)
            .attr("y", node => node.y0)
            .attr("width", node => node.x1 - node.x0)
            .attr("height", node => Math.max(1, node.y1 - node.y0))
            .attr("rx", 3)
            .attr("fill", node => colorByNode.get(node.id));

        nodes.append("text")
            .attr("x", node =>
                node.stage === 3 ? node.x0 + 24 : node.x0 - 8
            )
            .attr("y", node => (node.y0 + node.y1) / 2)
            .attr("dy", "0.35em")
            .attr("text-anchor", node =>
                node.stage === 3 ? "start" : "end"
            )
            .attr("fill", "#E6E4FA")
            .attr("font-size", 14)
            .text(node => node.label);

        nodes.append("title")
            .text(node =>
                `${node.label}: ${node.value} product(s)`
            );
    } else {
        sankeyContainer.appendChild(
            makeElement(
                "p",
                "Product flow will appear when related-product data is available.",
                "signal-caption"
            )
        );
    }


    sankeyPanel.appendChild(sankeyContainer);

    charts.append(
        barPanel,
        donutPanel,
        sankeyPanel,
        signalPanel,
        relatedPanel,
        insightsPanel
    );
    results.appendChild(charts);

    // Animated comparison of AI-assessed related products
    const relatedProducts = Array.isArray(data.related_products)
        ? data.related_products.filter(
            (item) =>
                item &&
                typeof item.name === "string" &&
                typeof item.value_score === "number" &&
                Number.isFinite(item.value_score)
        ).slice(0, 6)
        : [];

    if (typeof Chart !== "undefined" && relatedProducts.length > 0) {

        const valueLabelPlugin = {
            id: "relatedValueLabels",
            afterDatasetsDraw(chart) {
                const { ctx } = chart;

                ctx.save();
                ctx.font = "bold 12px Arial";
                ctx.fillStyle = "#e2e8f0";
                ctx.textAlign = "left";
                ctx.textBaseline = "middle";

                chart.getDatasetMeta(0).data.forEach((bar, index) => {
                    const score = chart.data.datasets[0].data[index];

                    ctx.fillText(
                        `${score}/100`,
                        bar.x + 8,
                        bar.y
                    );
                });

                ctx.restore();
            }
        };

        relatedChart = new Chart(relatedCanvas, {
            type: "bar",
            data: {
                labels: relatedProducts.map((item) => item.name),
                datasets: [{
                    label: "AI Value Score",
                    data: relatedProducts.map((item) =>
                        Math.max(0, Math.min(100, item.value_score))
                    ),

                    backgroundColor: ["#78DCFF","#A78BFA","#FFD400","#F472B6","#5EEAD4","#60A5FA"],

                    borderRadius: 9,
                    borderSkipped: false,
                    barThickness: 18,
                    clip: false
                }]
            },
            options: {
                indexAxis: "y",
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 1800,
                    easing: "easeOutQuart"
                },

                layout: {
                    padding: {
                        right: 42
                    }
                },

                plugins: {
                    legend: {
                        display: false
                    },
                    


                    tooltip: {
                        callbacks: {
                            label: (context) =>
                                `AI-assessed value: ${context.parsed.x}/100`,

                            afterLabel: (context) => {
                                const product = relatedProducts[context.dataIndex];

                                return product?.score_reason
                                    ? `Reason: ${product.score_reason}`
                                    : "Reason: Not available";
                            }
                        }
                    },

                    title: {
                        display: true,
                        text: "AI Value Score (0–100) — Subjective Assessment",
                        color: "#cbd5e1",
                        font: {
                            size: 12
                        },
                        padding: {
                            bottom: 16
                        }
                    }

                },
                scales: {
                    x: {
                        min: 0,
                        max: 100,
                        grid: {
                            color: "rgba(148, 163, 184, 0.1)"
                        },
                        ticks: {
                            color: "#94a3b8"
                        }
                    },
                    y: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: "#cbd5e1"
                        }
                    }
                }
            },
            plugins: [valueLabelPlugin]
        });
    } else {
        relatedPanel.appendChild(
            makeElement(
                "p",
                "Related product scores will appear when research data is available.",
                "signal-caption"
            )
        );
    }




    if (typeof Chart !== "undefined" && offers.length) {


        // Animated AI Market Signal — illustrative visualization

        // Product-specific illustrative signal, not measured history
        const productKey = String(data.product || "product");

        let seed = 0;
        for (const character of productKey) {
            seed = (seed * 31 + character.charCodeAt(0)) >>> 0;
        }

        const signalValues = Array.from({ length: 10 }, (_, index) => {
            const wave = Math.sin(index * 1.7 + seed % 10) * 12;
            const trend = 30 + index * 6;
            const variation = ((seed >>> (index % 16)) % 11) - 5;

            return Math.max(
                10,
                Math.min(95, Math.round(trend + wave + variation))
            );
        });


        const signalContext = signalCanvas.getContext("2d");

        const signalGradient = signalContext.createLinearGradient(
            0, 0, 0, 300
        );
        signalGradient.addColorStop(0, "rgba(120, 220, 255, 0.35)");
        signalGradient.addColorStop(1, "rgba(167, 139, 250, 0.02)");

        signalChart = new Chart(signalCanvas, {
            type: "line",

            data: {
                labels: relatedProducts.map(item => item.name),
                datasets: [{
                    label: "AI Value Score",
                    data: relatedProducts.map(item =>
                        Math.max(0, Math.min(100, item.value_score))
                    ),

                    borderColor: "#78DCFF",
                    backgroundColor: signalGradient,
                    borderWidth: 4,
                    fill: true,
                    tension: 0.45,
                    pointRadius: 0,
                    pointHoverRadius: 6,
                    pointHoverBackgroundColor: "#FFD400"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 2200,
                    easing: "easeInOutQuart"
                },

                plugins: {
                    legend: { display: false },
                    title: {
                        display: true,
                        text: "AI-Assessed Product Value (0–100)",
                        color: "#cbd5e1",
                        font: {
                            size: 13
                        },
                        padding: {
                            bottom: 16
                        }
                    },

                    tooltip: {
                        callbacks: {
                            title: items =>
                                items[0]?.label || "Product",

                            label: context =>
                                `AI Value Score: ${context.parsed.y}/100`,

                            afterLabel: context => {
                                const product = relatedProducts[context.dataIndex];

                                return product?.score_reason
                                    ? `Reason: ${product.score_reason}`
                                    : "Reason: Not available";
                            }
                        }
                    }

                },

                scales: {

                    x: {
                        ticks: {
                            color: "#C9C3F5",
                            maxRotation: 0,
                            minRotation: 0,
                            autoSkip: false,
                            callback: function (value) {
                                const label = this.getLabelForValue(value);
                                return label.length > 18
                                    ? label.slice(0, 16) + "…"
                                    : label;
                            }
                        },
                        grid: {
                            display: false
                        }
                    },

                    y: {
                        min: 0,
                        max: 100,
                        ticks: { color: "#C9C3F5" },
                        grid: { color: "rgba(148,163,184,0.12)" }
                    }
                }
            }
        });


        const rankedOffers = [...offers].sort(
            (a, b) => a.price - b.price
        );

        priceChart = new Chart(barCanvas, {
            type: "bar",
            data: {
                labels: rankedOffers.map(o => o.retailer),
                datasets: [{
                    label: "AI-reported price (USD)",
                    data: rankedOffers.map(o => o.price),
                    backgroundColor: rankedOffers.map((offer, index) => {
                        const palette = ["#78DCFF","#A78BFA","#FFD400","#F472B6","#5EEAD4","#60A5FA"];
                        if (index === 0) return "#FF8A3D"; // best price
                        return palette[(index - 1) % palette.length];
                    }),
                    hoverBackgroundColor: (context) => {
                        return context.dataset.backgroundColor[context.dataIndex];
                    },
                    borderRadius: 8,
                    barThickness: 24
                }]
            },
            options: {
                indexAxis: "y",
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 1400
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: context =>
                                `$${context.parsed.x.toFixed(2)} — AI-reported`
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            color: "#C9C3F5",
                            callback: value => "$" + value
                        },
                        grid: {
                            color: "rgba(255,255,255,0.12)"
                        }
                    },
                    y: {
                        ticks: {
                            color: "#e0f2fe",
                            font: {
                                size: 15,
                                weight: "bold"
                            }
                        },
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });




        const directCount = offers.filter(o => {
            if (o.verification !== "direct_listing") return false;

            try {
                const source = new URL(o.source_url);
                const listing = new URL(o.url);

                return (
                    ["http:", "https:"].includes(source.protocol) &&
                    ["http:", "https:"].includes(listing.protocol) &&
                    source.hostname === listing.hostname
                );
            } catch {
                return false;
            }
        }).length;

        const totalCount = offers.length;

        donutCenter.append(
            makeElement("strong", `${directCount}/${totalCount}`),
            makeElement("span", "DIRECT")
        );



        const reportedCount = offers.filter(
            o => o.verification === "third_party_report"
        ).length;

        const otherCount = Math.max(
            0,
            totalCount - directCount - reportedCount
        );


        verificationChart = new Chart(donutCanvas, {
            type: "doughnut",
            data: {
                labels: [
                    "Direct listing reported",
                    "Third-party report",
                    "Unverified / unknown"
                ],
                datasets: [{
                    data: [directCount, reportedCount, otherCount],
                    backgroundColor: ["#5EEAD4", "#78DCFF", "#FFD400"],
                    hoverBackgroundColor: ["#5EEAD4", "#78DCFF", "#FFD400"],
                    hoverOffset: 12,
                    spacing: 3,
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                cutout: "68%",
                animation: { duration: 1400 },
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: {
                            color: "#e0f2fe",
                            font: { size: 13 },
                            padding: 15
                        }
                    }
                }
            }
        });
    }

    // RETAILER SOURCES
    results.appendChild(makeElement("h4", "Retailer Sources"));

    for (const offer of data.offers) {
        const row = document.createElement("div");
        row.className = "source-row";

        const priceText =
            typeof offer.price === "number" && Number.isFinite(offer.price)
                ? `$${offer.price.toFixed(2)}`
                : "Price unavailable";

        row.appendChild(
            makeElement(
                "strong",
                `${offer.retailer || "Unknown retailer"} — ${priceText}`
            )
        );


        const hasUsableSource = (() => {
            try {
                const source = new URL(offer.source_url);
                return (
                    source.protocol === "https:" ||
                    source.protocol === "http:"
                );
            } catch {
                return false;
            }
        })();


        let verificationLabel = " · AI-reported — not independently verified";

        if (!hasUsableSource) {
            verificationLabel = " · Source missing — not independently verified";
        } else if (offer.verification === "third_party_report") {
            verificationLabel = " · Third-party report — not independently verified";
        } else if (offer.verification === "direct_listing") {
            verificationLabel = " · Direct listing reported — not independently verified";
        }


        const liveStatus = offer.live_price_check?.status;

        if (liveStatus === "network_disabled") {
            verificationLabel += " (live verification safely disabled)";
        } else if (liveStatus === "no_retailer_url") {
            verificationLabel += " (retailer URL unavailable)";
        } else if (liveStatus === "not_checked") {
            verificationLabel += " (live check not performed)";
        }



        row.appendChild(
            makeElement("span", verificationLabel)
        );



        const sourceUrl =
            typeof offer.source_url === "string"
                ? offer.source_url.trim()
                : "";

        let validSource = null;

        try {
            const parsedUrl = new URL(sourceUrl);

            if (
                parsedUrl.protocol === "https:" ||
                parsedUrl.protocol === "http:"
            ) {
                validSource = parsedUrl.href;
            }
        } catch {
            // No usable source URL was provided.
        }

        if (validSource) {
            const link = document.createElement("a");
            link.href = validSource;
            link.textContent = "↗ View price source";
            link.target = "_blank";
            link.rel = "noopener noreferrer";
            row.appendChild(link);
        } else {
            const warning = makeElement(
                "div",
                "⚠ Source link unavailable — price not independently verified",
                "source-warning"
            );

            row.appendChild(warning);
        }


        results.appendChild(row);
    }

    // PRODUCT SPECS
    results.appendChild(makeElement("h4", "Product Specifications"));

    const specs = document.createElement("div");
    specs.className = "specs-grid";

    for (const [key, value] of Object.entries(data.specifications || {})) {
        const card = document.createElement("div");
        card.className = "spec-card";
        card.append(
            makeElement("span", key.replaceAll("_", " ").toUpperCase()),
            makeElement("strong", String(value ?? "N/A"))
        );
        specs.appendChild(card);
    }

    results.appendChild(specs);

    // AI RECOMMENDATION

    const recommendationCard = document.createElement("div");
    recommendationCard.className = "ai-recommendation-card";

    const recommendationHeader = document.createElement("div");
    recommendationHeader.className = "ai-recommendation-header";

    const recommendationIcon = makeElement(
        "div",
        "✦",
        "ai-recommendation-icon"
    );

    const recommendationTitles = document.createElement("div");
    recommendationTitles.append(
        makeElement("h4", "AI BUYING RECOMMENDATION"),
        makeElement("span", "PRICE SCOUT INTELLIGENCE")
    );

    recommendationHeader.append(
        recommendationIcon,
        recommendationTitles
    );


    const allOffersHaveSources =
        offers.length > 0 &&
        offers.every(offer => {
            try {
                const url = new URL(offer.source_url);
                return url.protocol === "https:" || url.protocol === "http:";
            } catch {
                return false;
            }
        });

    const recommendationMessage = allOffersHaveSources
        ? (
            data.recommendation ||
            "Review the retailer offers before purchasing."
        )
        : (
            "⚠ PRICE VERIFICATION NEEDED\n\n" +
            "The AI found reported prices, but one or more offers " +
            "lack usable source links.\n\n" +
            "The lowest reported price is not yet a confirmed deal. " +
            "Check the retailer's actual product page and final " +
            "checkout price before making a purchase."
        );

    const recommendationText = makeElement(
        "p",
        recommendationMessage,
        "ai-recommendation-text"
    );


    const recommendationFooter = makeElement(
        "div",
        "✓ Review source links, seller reputation, warranty, and final checkout price.",
        "ai-recommendation-footer"
    );

    recommendationCard.append(
        recommendationHeader,
        recommendationText,
        recommendationFooter
    );

    results.appendChild(recommendationCard);
    // Move specifications and recommendation to the top
    const researchSummary = document.createElement("div");
    researchSummary.className = "chart-panel research-summary-panel";

    researchSummary.append(
        specs.previousElementSibling,
        specs,
        recommendationCard
    );

    results.prepend(researchSummary);
}
