try {
        // News logic
        const newsBtn = "dummy";
        const newsIndicator = { classList: { remove: () => {}, add: () => {} } };
        const newsContainer = { set innerHTML(val) {} };
        const newsFilters = { addEventListener: () => {} };
        
        let currentNewsCategory = 'ALL';

        async function fetchFinanceNews(category = 'ALL') {
            currentNewsCategory = category;
            
            try {
                const response = await fetch(`/api/news?category=${category}`);
                const data = await response.json();
                
                if (data.status === 'success') {
                    renderNews(data.news);
                    if(category === 'ALL') updateSentimentBlink(data.news);
                }
            } catch (error) {
                console.error("News fetch error:", error);
            }
        }

        function renderNews(articles) {
            if (articles.length === 0) {
                return;
            }

            const html = articles.map(article => {
                const trendIcon = article.trend === 'Bullish' ? '📈' : article.trend === 'Bearish' ? '📉' : '↔️';
                const trendColor = article.trend === 'Bullish' ? 'text-success' : article.trend === 'Bearish' ? 'text-danger' : 'text-secondary';
                const impactColor = article.impact === 'HIGH' ? 'text-danger' : article.impact === 'MEDIUM' ? 'text-warning' : 'text-info';
                
                return `
                <div class="news-item">
                    <div class="news-meta-row">
                        <div>
                            <span class="news-badge bg-primary text-white">${article.category}</span>
                            <span class="text-muted small">${article.time} | ${article.source}</span>
                        </div>
                        <div class="impact-tag ${impactColor}">
                            ${article.impact === 'HIGH' ? '🔥' : '⚡'} IMPACT: ${article.impact}
                        </div>
                    </div>
                    
                    <h6 class="fw-bold mb-2" style="font-size: 1.1rem; line-height: 1.4;">${article.title}</h6>
                    
                    <div class="d-flex align-items-center gap-3 small">
                        <span class="fw-bold ${article.sentiment_color === 'success' ? 'text-success' : 'text-danger'}">
                            Sentiment: ${article.sentiment} ${article.sentiment === 'Positive' ? '✅' : '❌'}
                        </span>
                        <span class="fw-bold ${trendColor}">
                            Trend: ${article.trend} ${trendIcon}
                        </span>
                    </div>

                    <div class="news-analysis">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <span class="small fw-bold text-uppercase text-secondary">AI Analysis</span>
                            <span class="badge ${article.ai_signal === 'BUY' ? 'bg-success' : article.ai_signal === 'SELL' ? 'bg-danger' : 'bg-secondary'} px-2">
                                SIGNAL: ${article.ai_signal} (${article.confidence})
                            </span>
                        </div>
                        <p class="small text-secondary mb-0"><strong>Affects:</strong> ${article.affects}. Based on sentiment analysis, target trend is ${article.trend}.</p>
                    </div>

                    <div class="news-action-btns">
                        <a href="https://www.google.com/search?q=${encodeURIComponent(article.title)}" target="_blank" class="news-btn-sm border text-body">View Details</a>
                        <a href="#" onclick="openTrade('${article.category}'); return false;" class="news-btn-sm bg-primary text-white">Trade Now 💸</a>
                    </div>
                </div>
            `;}).join('');
        }

        function openTrade(cat) {
            // Smart redirection based on news category
            if(cat === 'CRYPTO') window.open('https://www.binance.com/', '_blank');
            else if(cat === 'METALS') window.open('https://www.moneycontrol.com/commodity/', '_blank');
            else window.open('https://web.angelone.in/', '_blank');
        }

        function updateSentimentBlink(articles) {
            const positives = articles.filter(a => a.sentiment === 'Positive').length;
            const negatives = articles.filter(a => a.sentiment === 'Negative').length;
        }

    console.log("Syntax check passed");
} catch(e) {
    console.log("Syntax error: " + e);
}
