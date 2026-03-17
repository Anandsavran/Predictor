// AI Chatbot UI Logic

document.addEventListener('DOMContentLoaded', () => {
    const chatbot = document.getElementById('ai-chatbot-widget');
    const closeBtn = document.getElementById('chatbot-close');
    const contentBody = document.getElementById('chatbot-main-content');
    const loader = document.getElementById('chatbot-loader');
    
    // Expand automatically after 7 seconds
    setTimeout(() => {
        if (!chatbot.classList.contains('expanded')) {
            expandChatbot();
            
            // Automatically close 5 seconds after it auto-opens
            setTimeout(() => {
                chatbot.classList.remove('expanded');
            }, 5000);
        }
    }, 7000);

    chatbot.addEventListener('click', (e) => {
        if (!chatbot.classList.contains('expanded')) {
            expandChatbot();
        }
    });

    closeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        chatbot.classList.remove('expanded');
    });

    function expandChatbot() {
        chatbot.classList.add('expanded');
        // Simulate API loading data
        if (contentBody.classList.contains('hidden')) {
            setTimeout(() => {
                loader.classList.add('hidden');
                contentBody.classList.remove('hidden');
                initPredictionCycle();
            }, 1000); // 1s fake load
        }
    }

    // Prediction Cycling Logic (Today -> 1W -> 1M -> 3M -> 6M -> 1Y)
    const timelines = [
        { label: "Today", mult: 1 },
        { label: "1 Week", mult: 2.5 },
        { label: "1 Month", mult: 5 },
        { label: "3 Months", mult: 12 },
        { label: "6 Months", mult: 20 },
        { label: "1 Year", mult: 40 }
    ];

    let cycleIndex = 0;
    let cycleInterval;
    let cachedPrices = {};

    async function fetchInitialPrices() {
        const symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK', 'SBIN', 'GC=F', 'SI=F', 'HG=F', 'BTC-USD', 'ETH-USD'];
        for (const symbol of symbols) {
            try {
                const res = await fetch(`/api/chatbot/predict/${encodeURIComponent(symbol)}`);
                const data = await res.json();
                if (data.status === 'success') {
                    cachedPrices[symbol] = data.data.current_price;
                    updatePriceDisplay(symbol, data.data.current_price);
                }
            } catch (err) {
                console.error(`Error fetching price for ${symbol}:`, err);
            }
        }
    }

    function updatePriceDisplay(symbol, price) {
        const cards = document.querySelectorAll(`.prediction-card[data-symbol="${symbol}"]`);
        const isCommodityOrCrypto = symbol.includes('=') || symbol.includes('-');
        const symbolPrefix = isCommodityOrCrypto ? '$' : '₹';
        
        cards.forEach(card => {
            const priceEl = card.querySelector('.prediction-current-price');
            if (priceEl) priceEl.textContent = `${symbolPrefix}${price}`;
        });
    }

    function updatePredictions() {
        const timeline = timelines[cycleIndex];
        document.querySelectorAll('.timeline-value').forEach(el => {
            el.textContent = timeline.label;
        });

        // Update values dynamically to simulate AI predictions scaling over time
        document.querySelectorAll('.prediction-card').forEach(card => {
            const symbol = card.getAttribute('data-symbol');
            const upValEl = card.querySelector('.prediction-value-up span.val');
            const downValEl = card.querySelector('.prediction-value-down span.val');
            const valEl = upValEl || downValEl;
            
            if (valEl) {
                const baseVal = parseFloat(valEl.getAttribute('data-base'));
                const pctChange = baseVal * timeline.mult;
                valEl.textContent = `${pctChange.toFixed(2)}%`;

                // Calculate and optionally show predicted price if we have current price
                if (cachedPrices[symbol]) {
                    const currentPrice = cachedPrices[symbol];
                    const direction = upValEl ? 1 : -1;
                    const predictedPrice = currentPrice * (1 + (direction * pctChange / 100));
                    // Update current price display to show predicted price
                    const priceEl = card.querySelector('.prediction-current-price');
                    if (priceEl) {
                        const isCommodityOrCrypto = symbol.includes('=') || symbol.includes('-');
                        const prefix = isCommodityOrCrypto ? '$' : '₹';
                        priceEl.innerHTML = `<span style="font-size:0.75rem; color:gray;">Pred:</span> ${prefix}${predictedPrice.toFixed(2)}`;
                    }
                }
            }
        });

        cycleIndex = (cycleIndex + 1) % timelines.length;
    }

    function initPredictionCycle() {
        // Fetch prices once when opened
        fetchInitialPrices();
        // Run once immediately
        updatePredictions();
        // Cycle every 3 seconds
        if(cycleInterval) clearInterval(cycleInterval);
        cycleInterval = setInterval(updatePredictions, 3000);
    }

    // Expand Stocks List
    const expandStocksBtn = document.getElementById('expand-stocks-btn');
    const hiddenStocks = document.getElementById('hidden-stocks-list');

    if(expandStocksBtn) {
        expandStocksBtn.addEventListener('click', () => {
            if (hiddenStocks.classList.contains('hidden')) {
                hiddenStocks.classList.remove('hidden');
                expandStocksBtn.innerHTML = 'Hide More Stocks <span>&#9650;</span>';
            } else {
                hiddenStocks.classList.add('hidden');
                expandStocksBtn.innerHTML = 'Show More Stocks <span>&#9660;</span>';
            }
        });
    }
    // Chat Search Logic
    const chatInput = document.querySelector('.chatbot-input');
    const chatSendBtn = document.querySelector('.chatbot-send');

    function appendMessage(text, isUser = false) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `chat-message ${isUser ? 'user-message' : 'bot-message'}`;
        msgDiv.innerHTML = text;
        contentBody.appendChild(msgDiv);
        contentBody.scrollTop = contentBody.scrollHeight;
    }

    function handleChatSearch() {
        const query = chatInput.value.trim();
        if(!query) return;
        
        chatInput.value = '';
        appendMessage(query, true);
        
        // Show loading
        const loadingId = 'loading-' + Date.now();
        const loadingHtml = `<div id="${loadingId}" class="chat-message bot-message" style="display:flex; align-items:center;">Searching for ${query}... <span class="spinner" style="display:inline-block; width:15px; height:15px; border-width:2px; margin-left:8px;"></span></div>`;
        contentBody.insertAdjacentHTML('beforeend', loadingHtml);
        contentBody.scrollTop = contentBody.scrollHeight;
        
        // Hide default cards if they are visible
        const defaultCards = document.querySelectorAll('.prediction-card, .expand-stocks-btn, .prediction-section-title:not(.search-title)');
        defaultCards.forEach(c => c.style.display = 'none');
        
        fetch(`/api/chatbot/predict/${encodeURIComponent(query)}`)
            .then(res => res.json())
            .then(data => {
                const loaderEl = document.getElementById(loadingId);
                if(loaderEl) loaderEl.remove();
                if(data.status === 'success') {
                    const result = data.data;

                    if (result.type === 'text') {
                        // AI Fallback Mode Handled
                        appendMessage(`🤖 AI: ${result.content}`);
                    } else {
                        // Stock Prediction Mode
                        const defaultPred = result.predictions['1 Year'];
                        
                        let signalColor = "gray";
                        if(result.signal.includes("BUY")) signalColor = "green";
                        if(result.signal.includes("SELL")) signalColor = "red";
                        
                        const cardHtml = `
                            <div class="search-result-card">
                                <div class="prediction-section-title search-title">${result.symbol}</div>
                                <div class="price-row">
                                    <span class="text-secondary" style="font-size:0.9rem;">Current Price:</span>
                                    <span class="current-price">₹${result.current_price}</span>
                                </div>
                                <div class="price-row mt-2 pt-2 border-top">
                                    <div>
                                        <span class="text-secondary" style="font-size:0.9rem;">Live Signal:</span>
                                        <span class="pred-pct" style="color: ${signalColor}; font-weight: bold;">${result.signal}</span>
                                    </div>
                                    <div style="font-size: 0.8rem; text-align: right; color: var(--bs-secondary-color);">
                                        RSI: ${result.rsi} <br/> M.A(50): ₹${result.ma}
                                    </div>
                                </div>
                                <div class="price-row mt-2 pt-2 border-top">
                                    <div>
                                        <span class="text-secondary" style="font-size:0.9rem;">Expected (1Y):</span>
                                        <span class="pred-pct">${defaultPred.pct > 0 ? '▲' : '▼'} ${defaultPred.pct}%</span>
                                    </div>
                                    <span class="pred-price">₹${defaultPred.price}</span>
                                </div>
                                <div style="font-size:0.75rem; margin-top:12px; color:gray; line-height: 1.3;">
                                    * AI Prediction based on MA/RSI Market Models.<br/><br/>
                                    <strong>Disclaimer:</strong> This platform is for educational purposes only. Not financial advice.
                                </div>
                            </div>
                        `;
                        appendMessage(`Here are your AI predictions & live signals for <strong>${result.symbol}</strong>:` + cardHtml);
                    }
                } else {
                    appendMessage("Sorry, I could not fetch predictions for that query. Please try again.");
                }
            })
            .catch(err => {
                const loader = document.getElementById(loadingId);
                if(loader) loader.remove();
                appendMessage("An error occurred while fetching the prediction.");
            });
    }

    if(chatSendBtn) {
        chatSendBtn.addEventListener('click', handleChatSearch);
    }
    
    if(chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            e.stopPropagation();
            if(e.key === 'Enter') handleChatSearch();
        });
        chatInput.addEventListener('keydown', (e) => {
            e.stopPropagation();
        });
    }
});
