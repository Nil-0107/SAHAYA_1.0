# ML Artifact Inspection Report

## Scope

This report inspects only the supplied artifacts:

- `tfidf_vectorizer(1)(1).joblib`
- `logistic_regression_emotion_model(1).joblib`

The files were loaded read-only with Joblib. They were not modified, retrained, re-saved, or used to create a risk score.

The repository copies under `backend/app/ml/artifacts/` have the same SHA-256 hashes as the supplied root artifacts:

| Artifact | SHA-256 |
|---|---|
| `tfidf_vectorizer(1)(1).joblib` | `9f08a8809baa607ca18e01b512f6ff3be3ab57d39cc54325d6b79305af2dde33` |
| `logistic_regression_emotion_model(1).joblib` | `a5f886726664782cf7bec27aa7a27be27f567d457a6b246514bbf6c6f23a19cd` |

The report separates **factually observed** properties from **inferences**. No class semantics are assigned.

---

# FACTUALLY OBSERVED

## 1. Classifier type

The classifier artifact is:

```text
sklearn.linear_model._logistic.LogisticRegression
```

Observed estimator parameters:

| Property | Observed value |
|---|---|
| Solver | `lbfgs` |
| Penalty | `l2` |
| Regularization `C` | `1.0` |
| `fit_intercept` | `True` |
| `max_iter` | `1000` |
| `tol` | `0.0001` |
| `class_weight` | `None` |
| `random_state` | `42` |
| `n_jobs` | `None` |
| `dual` | `False` |
| `warm_start` | `False` |
| `multi_class` | `deprecated` |
| `n_iter_` | `[126]` |

Observed fitted attributes:

- `classes_` is present.
- `coef_` is present with shape `(6, 5000)` and dtype `float64`.
- `intercept_` is present with shape `(6,)`.
- `n_features_in_` is `5000`.
- `n_iter_` is present.
- `predict` exists.
- `predict_proba` exists.
- `decision_function` exists.

## 2. Vectorizer type

The vectorizer artifact is:

```text
sklearn.feature_extraction.text.TfidfVectorizer
```

Observed estimator parameters:

| Property | Observed value |
|---|---|
| `input` | `content` |
| `encoding` | `utf-8` |
| `decode_error` | `strict` |
| `dtype` | `numpy.float64` |
| `analyzer` | `word` |
| `ngram_range` | `(1, 1)` |
| `lowercase` | `True` |
| `preprocessor` | `None` |
| `tokenizer` | `None` |
| `stop_words` | `None` |
| `strip_accents` | `None` |
| `token_pattern` | `(?u)\b\w\w+\b` |
| `max_features` | `5000` |
| `min_df` | `1` |
| `max_df` | `1.0` |
| `norm` | `l2` |
| `use_idf` | `True` |
| `smooth_idf` | `True` |
| `sublinear_tf` | `False` |
| `binary` | `False` |
| `vocabulary` constructor parameter | `None` |

Observed fitted attributes:

- `vocabulary_` is present.
- `idf_` is present.
- `_tfidf` is a fitted `TfidfTransformer`.
- `_tfidf.n_features_in_` is `5000`.
- `get_feature_names_out()` returns `5000` feature names.
- `fixed_vocabulary_` is `False`.

## 3. Number of classes

The classifier contains **6 classes**.

This is directly observed from `classes_`, `coef_`, `intercept_`, and probability output shape.

## 4. Class IDs

The observed class IDs are:

```text
[0, 1, 2, 3, 4, 5]
```

`classes_` has NumPy integer values.

## 5. Class names

No semantic class names are stored in the classifier artifact.

The following were not present:

- A class-name mapping attribute.
- Human-readable class labels.
- A `feature_names_in_` attribute.
- Artifact metadata identifying the meaning of IDs `0` through `5`.

Therefore, the semantic meaning of each class ID is **unknown**.

## 6. Feature dimensions

The classifier expects exactly:

```text
5000 input features
```

Observed from:

- `classifier.n_features_in_ == 5000`
- `classifier.coef_.shape == (6, 5000)`
- `vectorizer.idf_.shape == (5000,)`

A read-only smoke check produced:

```text
vectorizer.transform(two_text_documents).shape == (2, 5000)
classifier.predict_proba(two_by_5000_matrix).shape == (2, 6)
```

## 7. Vocabulary size

The fitted vocabulary contains exactly:

```text
5000 terms
```

Observed properties:

- `len(vectorizer.vocabulary_) == 5000`
- Vocabulary indices range from `0` through `4999`.
- All `5000` indices are unique.
- The vectorizer has `max_features=5000`.
- `idf_` contains `5000` values.

The artifact does not retain the original untruncated training vocabulary. Only the fitted 5000-term vocabulary is available.

## 8. Preprocessing assumptions supported by the artifact configuration

The fitted vectorizer is configured to perform the following operations:

1. Accept document content.
2. Decode input as UTF-8 with strict error handling.
3. Convert text to lowercase.
4. Use word-level analysis.
5. Use unigrams only.
6. Match Unicode word tokens containing at least two word characters.
7. Do not apply a custom preprocessor.
8. Do not apply a custom tokenizer.
9. Do not apply a built-in or custom stop-word list.
10. Do not strip accents.
11. Count term frequencies.
12. Do not binarize term frequencies.
13. Do not apply sublinear term-frequency scaling.
14. Apply inverse document frequency.
15. Use smoothed IDF.
16. L2-normalize each transformed document.
17. Restrict output to the fitted 5000-term vocabulary.

The artifacts do not show any additional text cleaning, translation, language detection, profanity handling, spelling correction, HTML removal, emoji handling, or application-specific preprocessing.

## 9. N-gram range

The observed n-gram range is:

```text
(1, 1)
```

This means unigrams only. No bigrams or trigrams are generated by this vectorizer.

## 10. `predict_proba`

The classifier has a callable `predict_proba` method.

A smoke check with two transformed text documents returned:

```text
Shape: (2, 6)
Row sums: approximately 1.0 for each row
```

The observed sample predictions were numeric classes `4` and `1`. These values are recorded only as an execution check and do not establish class semantics.

## 11. Expected input format

### Vectorizer input

The observed vectorizer configuration uses `input="content"`. Its direct input is therefore a collection of raw text documents, normally Python strings.

Example structural form:

```python
vectorizer.transform([
    "first raw text document",
    "second raw text document",
])
```

The returned object is a sparse TF-IDF matrix. The artifact configuration does not define a JSON request schema.

### Classifier input

The observed classifier expects a numeric feature matrix with exactly `5000` columns in the same feature order as the fitted vectorizer.

The corresponding structural flow is:

```text
raw text documents
→ fitted TfidfVectorizer.transform
→ sparse matrix with shape (documents, 5000)
→ LogisticRegression.predict_proba
```

The classifier does not accept raw text directly.

## 12. Is the vectorizer already fitted?

**Yes.**

Evidence:

- `vocabulary_` exists.
- `idf_` exists.
- `_tfidf.n_features_in_` exists.
- `get_feature_names_out()` returns fitted feature names.
- `transform()` returns a 5000-column matrix without fitting the vectorizer.

Calling `fit()` or `fit_transform()` on this artifact would create a new vocabulary and is not part of the observed inference contract.

## 13. Is the classifier already fitted?

**Yes.**

Evidence:

- `classes_` exists.
- `coef_` exists.
- `intercept_` exists.
- `n_features_in_` exists.
- `n_iter_` records fitting iterations.
- `predict()` and `predict_proba()` return results without fitting.

## 14. Compatibility and version observations

Inspection was performed with:

| Runtime component | Version |
|---|---|
| Python | `3.14.7` |
| scikit-learn | `1.9.0` |
| Joblib | `1.6.0` |
| NumPy | `2.4.6` |
| SciPy | `1.17.1` |

Both artifacts loaded, but scikit-learn emitted `InconsistentVersionWarning` stating that the estimators were persisted from **scikit-learn 1.6.1** and were being unpickled with **scikit-learn 1.9.0**.

Observed warnings included:

```text
Trying to unpickle estimator TfidfTransformer from version 1.6.1 when using version 1.9.0.
Trying to unpickle estimator TfidfVectorizer from version 1.6.1 when using version 1.9.0.
Trying to unpickle estimator LogisticRegression from version 1.6.1 when using version 1.9.0.
```

The smoke inference completed under the mismatched runtime, but successful loading does not prove exact cross-version reproducibility.

For strict reproduction, the observed persistence version indicates that a controlled scikit-learn `1.6.1` environment should be validated first. A future migration should explicitly load, verify, and re-export both artifacts together under one pinned runtime rather than silently relying on cross-version behavior.

Joblib artifacts use Python serialization. They must only be loaded from trusted sources.

---

# INFERRED

The following statements are reasonable inferences from the observed object types and dimensions, but are not embedded class semantics or training documentation.

1. The intended inference pipeline is likely raw text → fitted TF-IDF vectorizer → fitted logistic classifier.
2. The 5000 vectorizer feature columns are likely intended to correspond directly to the classifier's 5000 input columns. Their exact dimensional agreement and the fact that both artifacts have identical hashes in the repository copies support this inference.
3. Because the vectorizer lowercases text and uses a two-or-more-character Unicode word-token pattern, inputs containing only one-character tokens, punctuation, or symbols will not contribute token features under the observed configuration.
4. Because the vocabulary is capped at 5000 features, terms absent from the fitted vocabulary will be ignored during inference.
5. The probability vector represents the classifier's classes `0` through `5`, but it does not represent named emotions or meanings unless an external, authoritative label mapping is supplied.
6. Using the same scikit-learn persistence version as the artifacts may reduce compatibility risk, but exact reproducibility has not been established by this inspection.

---

# UNKNOWN OR NOT ESTABLISHED

The artifacts do not establish:

- What class IDs `0` through `5` mean.
- Whether the classes represent emotions, topics, sentiment, writing categories, or another target.
- Any mapping from class IDs to clinical, distress, legal, safety, or protective concepts.
- Any valid probability threshold.
- Whether probabilities are calibrated.
- Training-corpus identity, size, language, or collection methodology.
- Train/validation/test split.
- Evaluation metrics.
- Class balance.
- Whether the artifact was intended for single-document or batch inference.
- Any application-specific preprocessing before the vectorizer.
- Any deterministic-priority policy.

---

# EXPLICIT NON-CONCLUSIONS

This inspection does **not** establish any of the following:

- Emotion is distress.
- Emotion is clinical risk.
- Emotion is legal risk.
- A numeric class is a diagnosis.
- A probability is a probability of harm, abuse, recidivism, suicide, distress, or case priority.
- Any class ID has a human-readable meaning.
- Any threshold can be used for automated escalation.

No risk score or risk mapping should be introduced from these artifacts alone. A separate, evidence-based policy would require authoritative class metadata, intended-use documentation, validation results, and an explicit governance decision.

No model artifact was modified during this inspection.
