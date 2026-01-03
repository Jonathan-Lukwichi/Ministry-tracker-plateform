# Ministry Analytics 2.0: Advanced AI & ML-Powered Insights

This document evolves the initial set of questions into a more sophisticated analytical framework, reflecting techniques used by experienced data scientists. The goal is to move from descriptive analytics ("what happened") to predictive and prescriptive insights ("what will happen" and "what should we do").

**Methodology Upgrade:** We will enhance the analysis by incorporating normalized scoring, regression and classification models, and Natural Language Processing (NLP) to extract intelligence from unstructured text like sermon transcripts and audience comments.

**Note:** The prompts below are more advanced. They assume the AI assistant can work with dataframes in memory, use libraries like `scikit-learn`, `nltk`, and `gensim`, and has the ability to fetch and process unstructured data like comments or transcripts.

---

## 1. Audience Engagement & Reach (Enhanced)

*Moving from simple views to a holistic understanding of engagement drivers.*

### **Question 1.1 (Refined):** Which sermon topics have the highest *normalized engagement score*?

**Expert Rationale:** Average view counts are flawed; they don't account for a video's age (older videos have more time to accumulate views) and they treat likes and comments as secondary. A normalized, weighted score gives a truer picture of impact.

**CLI Prompt:**
```
Perform a robust analysis of topic engagement in `ministry_videos.db`.
1.  Load the `videos` table into a pandas DataFrame.
2.  For each video, calculate a `days_online` feature from the `upload_date`.
3.  Calculate a 'Normalized Engagement Score' using the formula:
    `Score = ((view_count / days_online) * 0.6) + (like_count * 0.3) + (comment_count * 0.1)`
4.  Group the DataFrame by `topic` and calculate the average `Normalized Engagement Score`.
5.  Present the results as a markdown table, sorted by the average score, showing the top and bottom 5 topics.
```

### **Question 1.2 (Refined):** What is the statistically significant relationship between sermon length and viewership?

**Expert Rationale:** Simple bucketing can miss the real trend. A regression analysis can model the relationship more accurately and identify points of diminishing returns.

**CLI Prompt:**
```
Analyze the relationship between video duration and views in `ministry_videos.db` using regression.
1.  Load `videos` into a DataFrame, filtering out any extreme outliers in `duration` or `view_count` that could skew the results.
2.  Perform a polynomial regression with `duration` as the independent variable and `view_count` as the dependent variable.
3.  Plot the resulting regression curve over a scatter plot of the data points.
4.  Provide a summary of the findings, stating the optimal duration range predicted by the model and the point at which viewership begins to show diminishing returns.
```

### **Question 1.3 (New - Predictive):** Can we predict if a new sermon will be a "Top Performer"?

**Expert Rationale:** Instead of just describing top videos, let's build a model that predicts them. This helps in pre-launch strategy. The model's "feature importance" will tell us the *drivers* of success.

**CLI Prompt:**
```
Build a classification model to predict high-performance videos.
1.  Load the `videos` table. Create a binary target variable `is_top_performer` (1 if `view_count` is in the top 20%, 0 otherwise).
2.  Use `topic`, `speaker_name`, `duration`, and `location` as features. Convert categorical features into dummy variables.
3.  Train a Logistic Regression or a Gradient Boosting classifier on an 80/20 train/test split of the data.
4.  Report the model's accuracy and F1-score on the test set.
5.  Most importantly, list the top 5 features that are most predictive of a video being a "top performer" based on the model's feature importance scores.
```

---

## 2. Advanced Content Intelligence (AI-Powered)

*Using Natural Language Processing (NLP) to understand the *content* and *reception* of sermons.*

### **Question 2.1 (New - NLP Topic Modeling):** What are the hidden, emergent themes in the pastor's sermons?

**Expert Rationale:** Pre-defined topic labels are limiting. Unsupervised topic modeling can analyze sermon transcripts to discover organic, underlying themes that may not be obvious. This reveals the ministry's true thematic DNA.

**CLI Prompt:**
```
Perform unsupervised topic modeling on sermon transcripts.
1.  (Requires transcript data) For all available sermon transcripts, preprocess the text: remove stop words, perform lemmatization.
2.  Use the preprocessed text to train a Latent Dirichlet Allocation (LDA) model with 5-7 topics.
3.  For each of the discovered topics, list the top 10 most representative words.
4.  Give each topic a human-readable name (e.g., "Topic 1: 'Grace, Forgiveness, Redemption...' -> 'Redemption & Grace'").
5.  Finally, create a table showing the prevalence of each discovered topic over the last three years to identify thematic shifts.
```

### **Question 2.2 (New - NLP Sentiment Analysis):** What is the emotional texture of our audience's comments?

**Expert Rationale:** Comment *count* is a shallow metric. Sentiment analysis of the comments themselves tells you if the engagement is positive and encouraging, or if it's controversial and questioning.

**CLI Prompt:**
```
Analyze the sentiment of YouTube comments for the top 10 most-viewed videos.
1.  (Requires comment data) Fetch the top 50-100 comments for each of the 10 most-viewed videos.
2.  For each comment, run a pre-trained sentiment analysis model (e.g., from the Hugging Face library) to classify it as 'Positive', 'Negative', or 'Neutral'.
3.  For each of the 10 videos, calculate the percentage distribution of positive, negative, and neutral comments.
4.  Present a summary table. Highlight any videos with an unusually high 'Negative' sentiment percentage, as they may warrant a pastoral review.
```

---

## 3. Predictive Operations & Growth

*Forecasting future trends and identifying strategic opportunities with greater precision.*

### **Question 3.1 (Refined):** Create a prioritized "Geospatial Opportunity Score" for future missions.

**Expert Rationale:** A simple "high views, no visit" model is good, but a weighted score is better. It should factor in not just raw viewership, but also the *growth* of that viewership, indicating rising interest.

**CLI Prompt:**
```
Generate a prioritized "Geospatial Opportunity Score" for potential mission locations.
1.  (Requires YouTube Analytics data) Get viewership data by city for the last 24 months.
2.  For each city, calculate two metrics: `total_views_L24M` (total views in the last 24 months) and `growth_rate` (percentage increase in views comparing the last 6 months to the prior 6 months).
3.  Filter out any city that has been a sermon `location` in `ministry_videos.db` in the last 18 months.
4.  Calculate a `Geospatial Opportunity Score` for the remaining cities: `Score = (log(total_views_L24M) * 0.5) + (growth_rate * 0.5)`.
5.  Display a ranked list of the top 5 cities by this score.
```

### **Question 3.2 (Refined):** What is the anomaly score for the pastor's monthly activity?

**Expert Rationale:** Instead of just flagging when all metrics are high, an anomaly detection model can find unusual patterns in the data that might indicate either burnout risk or a highly effective, replicable new working rhythm.

**CLI Prompt:**
```
Apply anomaly detection to the pastor's monthly activity to identify unusual patterns.
1.  Create a monthly time-series DataFrame with features: `sermon_count`, `total_trips`, `avg_sermon_duration`.
2.  Train an Isolation Forest or a Local Outlier Factor (LOF) model on this data.
3.  Use the model to calculate an `anomaly_score` for each month in the dataset.
4.  Plot the `sermon_count` over time, and use a different color to highlight the top 5% of months with the worst anomaly scores.
5.  List the dates of these anomalous months for leadership review.
```
