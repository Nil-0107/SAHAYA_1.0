# SAHAYA ML Implementation Audit

## Artifacts

The runtime uses the supplied fitted artifacts copied into the backend artifact directory:

- `backend/app/ml/artifacts/tfidf_vectorizer.joblib`
- `backend/app/ml/artifacts/logistic_regression_emotion_model.joblib`

The repository root also contains the uploaded source copies. The runtime copies are the controlled application inputs and are not replaced by another model.

## Pipeline

```text
validated check-in text
  → fitted TF-IDF vectorizer.transform
  → fitted logistic regression predict/predict_proba
  → numeric class and optional confidence
  → Checkin database record
  → authenticated frontend history
```

The application does not:

- Refit the vectorizer
- Retrain the classifier
- Generate random predictions
- Use keyword matching for ML classes
- Use Gemini for classification
- Convert output into diagnosis, danger, risk, legal, or severity meaning

## Lifecycle

`backend/app/ml/loader.py` uses a thread-safe process-local lazy singleton. Each artifact is loaded once per process. Validation requires:

- A fitted TF-IDF vectorizer
- `max_features=5000`
- 5000 learned vocabulary features
- A fitted classifier
- Numeric classes `{0, 1, 2, 3, 4, 5}`
- 5000 classifier input features

A missing or incompatible artifact returns a controlled unavailable error. Provider/model internals are not returned to the browser.

## Persisted output

`Checkin` stores:

- Numeric predicted class
- Semantic label, which remains `null` for this artifact
- Confidence when supported by `predict_proba`
- Model version/artifact ID
- Analysis status
- Timestamp and optional case link

The API returns the same actual values. The frontend displays numeric class and confidence only when present.

## Safety boundary

The ML artifact is an emotion classification model. SAHAYA does not claim that its numeric classes represent clinical distress, abuse, danger, legal category, or future probability. The separate administrative priority engine uses only approved structured case/support facts and never consumes ML output.

## Tests

Existing tests cover:

- Real artifact loading once
- Actual inference
- Numeric class and null semantic label
- Probability/no-probability behavior
- Invalid input
- Missing/corrupt artifact handling
- Safe unavailable errors

Current runtime warnings remain for the artifact persistence-version difference between the training and installed scikit-learn environments.

## Known limitations

- Joblib artifacts are pickle-based and do not have a signed manifest.
- The lazy loader does not currently run at process startup; it validates on first use.
- The process-local singleton is not a multi-process model registry.
- No model registry table is present.
- Check-in inference is synchronous.
- The artifact does not provide verified semantic labels.

These limitations are documented rather than represented as implemented functionality.
