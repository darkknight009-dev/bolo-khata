# Bharat Voice Crash Test

## Product Requirements Document (PRD)

**Document status:** MVP specification\
**Version:** 1.0\
**Prepared:** 28 October 2026\
**Target build window:** 28 October--9 November 2026\
**Challenge context:** Great Indian AI Internship Challenge\
**Product type:** Browser-based voice AI evaluation and robustness
testing platform\
**Primary platform:** Responsive web application\
**Proposed stack:** Next.js App Router + TypeScript

------------------------------------------------------------------------

## 1. Executive Summary

**Bharat Voice Crash Test** is a browser-based test lab that helps
builders understand how reliably a speech-recognition or voice-AI
workflow handles Indian English, Hindi, Hinglish, code-switching, fast
speech, and challenging acoustic conditions.

A user records or uploads a short audio clip, supplies the expected
transcript, selects a test condition, and runs the clip through a
configured speech-to-text (STT) provider. The platform compares the
provider's transcript with the expected transcript, measures errors,
highlights important entity mistakes, and produces a clear test report.

The product is not merely a transcription demo. Its central value is
**reproducible failure discovery**: the user can compare the same
utterance across conditions and see where recognition quality degrades.
It must distinguish actual provider results from locally simulated audio
transformations and must never invent benchmark results.

### Product promise

> **Break the audio. Measure the failure. Find what needs fixing.**

### MVP outcome

By the end of the MVP, a judge should be able to: 1. Open the app
without installing anything. 2. record or upload a short Hindi, English,
or Hinglish utterance. 3. enter the reference transcript and optional
critical details such as names, dates, amounts, and places. 4. run a
baseline transcription and selected robustness tests. 5. compare the
expected transcript with actual output. 6. see a transparent scorecard
with word error rate (WER), character error rate (CER) where
appropriate, entity preservation, latency, and test status. 7. inspect a
report showing which test condition caused which errors. 8. export or
share a compact test report.

The MVP can operate without telephony, a paid phone number, or a live
phone call.

------------------------------------------------------------------------

## 2. Problem Statement

Speech interfaces are increasingly used for customer support, booking,
collections, commerce, and other real-world workflows. In Indian
contexts, a voice system may encounter: - Hindi-English code-switching
within a sentence. - Indian names, locations, dates, phone-like digit
sequences, and currency amounts. - Regional pronunciation and varied
speaking speed. - Background noise, low recording volume, clipping, and
compressed audio. - Differences between clean microphone recordings and
difficult real-world audio.

A transcript that sounds broadly correct may still corrupt a critical
value. For example, a system may understand a sentence but misrecognize
an order amount, date, or proper noun. A single average accuracy score
can hide these failures.

Builders need a lightweight way to test representative utterances,
compare conditions, inspect errors, and repeat the same tests after
changing a model or configuration.

### Current product gap to address

The MVP should address the general developer need for a transparent,
repeatable test harness. It must **not** claim that a particular
provider has a known defect unless supported by reproducible evidence.
It should also avoid claiming that locally added synthetic noise is
equivalent to real telephone-network audio.

------------------------------------------------------------------------

## 3. Vision and Product Principles

### Vision

Make voice AI quality visible and testable for the languages and
speaking styles used across India.

### Principles

1.  **Evidence over hype:** every metric must be derived from recorded
    inputs and actual outputs.
2.  **Reproducibility:** preserve the test configuration, reference
    transcript, transformation settings, provider/model identifier where
    available, and timestamp.
3.  **Indian-language-first:** design test scenarios for Hindi, English,
    Hinglish, and expandable Indian language coverage.
4.  **Transparent simulation:** label synthetic noise, speed changes,
    and other transformations as simulated conditions.
5.  **Privacy by default:** do not make recordings public; minimise
    retention and provide deletion controls.
6.  **Provider-aware, not provider-locked:** build a provider adapter so
    the product can support a configured Gnani.ai STT API and
    potentially other providers later.
7.  **Honest evaluation:** do not compare results across different
    models as if the conditions were identical unless the differences
    are explicitly disclosed.
8.  **MVP discipline:** prioritise one end-to-end test workflow over a
    large but shallow feature set.

------------------------------------------------------------------------

## 4. Goals and Non-Goals

### 4.1 Goals

-   Provide a polished browser experience for recording and testing
    short audio clips.
-   Support audio upload and microphone capture on compatible browsers.
-   Use a real configured STT API for transcription when credentials are
    available.
-   Let users enter or correct the expected transcript.
-   Compute transparent text-comparison metrics.
-   Provide reproducible baseline-versus-challenged comparisons.
-   Include a small, curated starter suite of Hindi, English, and
    Hinglish examples.
-   Provide explainable error highlighting and critical-entity checks.
-   Keep API keys server-side.
-   Make the MVP demonstrable with a low number of paid API calls.
-   Make the app useful even when no provider key is configured by
    supporting a clearly labelled demo mode with fixture results.

### 4.2 Non-goals for the MVP

-   Answering or intercepting actual cellular calls.
-   Telephony, SIP, carrier integrations, or buying a phone number.
-   Building a new speech-recognition model.
-   Claiming to certify a model or guarantee production readiness.
-   A full real-time conversational voice agent.
-   Training or fine-tuning foundation models.
-   Large-scale public leaderboards or statistically representative
    national benchmarks.
-   Automatic accent, ethnicity, or demographic inference.
-   Speaker identification, voice biometrics, or deepfake detection.
-   Enterprise SSO, team billing, or complex multi-tenant
    administration.
-   A claim that synthetic audio tests accurately reproduce every
    real-world acoustic environment.

------------------------------------------------------------------------

## 5. Target Users and Jobs to Be Done

### Primary persona: Voice AI developer

**Needs:** Quickly test whether a model handles the language patterns
and acoustic conditions relevant to their application.

**Job to be done:** "When I change a speech model or configuration, help
me find regressions in representative utterances before I ship."

### Secondary persona: Hackathon judge or evaluator

**Needs:** Understand the product's value in a short demo and verify
that its results are real.

**Job to be done:** "Show me a clear example of a voice system failing,
how you measured it, and how the tool helps investigate it."

### Secondary persona: Product/QA engineer

**Needs:** Maintain a small regression suite and compare results between
test runs.

**Job to be done:** "Let me rerun the same test cases and see which
outputs changed."

### Not the target user for MVP

General consumers looking for a general-purpose voice assistant. This is
a testing and developer tool, not a consumer assistant.

------------------------------------------------------------------------

## 6. Core User Journeys

### Journey A --- First test

1.  User opens the landing page.
2.  Selects **Start a Crash Test**.
3.  Records a clip or uploads an audio file.
4.  Enters the expected transcript, or selects a labelled sample case.
5.  Selects a language label: Hindi, English, Hinglish/code-mixed, or
    Unknown/Mixed.
6.  Chooses a baseline run.
7.  The server sends audio to the configured STT provider.
8.  The UI displays the actual transcript, elapsed time, provider/model
    information when available, and status.
9.  The evaluation engine compares reference and hypothesis.
10. User sees metrics, differences, and critical-detail checks.

### Journey B --- Test robustness

1.  User opens an existing test case or creates one.
2.  Selects one or more local transformations, such as mild background
    noise or a speed adjustment.
3.  Reviews the transformation settings before running.
4.  App creates transformed audio in the browser or a controlled server
    process.
5.  Each transformed variant is sent to the STT provider only after user
    confirmation.
6.  Results are grouped under the original test case.
7.  User compares baseline and challenged variants.
8.  The app highlights transcript differences and any changed critical
    entities.

### Journey C --- Demo mode

1.  User opens the demo workspace.
2.  Selects a preloaded sample scenario.
3.  The app displays a precomputed, clearly labelled fixture run.
4.  UI labels the results **Demo data --- not generated by a live
    provider call**.
5.  User can explore the comparison interface without consuming API
    credits.

### Journey D --- Export report

1.  User opens a completed test run.
2.  Selects Export.
3.  App generates a JSON or CSV report; a printable report view may be
    used for PDF printing.
4.  Report includes test configuration, metrics, provider status,
    limitations, and whether audio was transformed.
5.  User downloads the file.

------------------------------------------------------------------------

## 7. Functional Requirements

Priority definitions: - **P0:** Must be in the challenge MVP. - **P1:**
Important if time allows. - **P2:** Post-MVP.

### 7.1 Landing page and navigation

**P0** - Explain the product in one sentence. - Provide a prominent
"Start a Crash Test" CTA. - Show the three-step workflow: Record →
Stress-test → Inspect. - Include an honest sample result with a visible
demo-data label if it is not live. - Explain supported test dimensions
and known limitations. - Provide navigation to Dashboard, Test Lab, Test
Suites, and About/Methodology.

**Acceptance criteria** - A first-time user can identify the product
purpose and start a test without onboarding. - No displayed sample
metric is represented as a live benchmark unless it is derived from a
real run.

### 7.2 Audio input

**P0** - Support microphone recording on browsers that expose the
MediaRecorder API. - Support audio file upload for common
browser-compatible formats. - Show recording duration, playback, and
file size. - Allow re-recording, replacing, or removing a clip. -
Validate file type and size before upload. - Display clear permission
and unsupported-browser errors. - Enforce a configurable short-clip
limit for MVP (recommended default: 30 seconds). - Let users explicitly
start an API run; do not automatically send audio immediately after
recording.

**P1** - Show waveform visualization. - Allow trimming a clip before
submission. - Add a preflight audio-quality warning for silence,
clipping, or very low volume where feasible.

**Acceptance criteria** - User can play back the selected audio before
submitting. - Unsupported files fail with a human-readable message. -
Microphone permission denial does not crash the page; upload remains
available.

### 7.3 Reference transcript and test metadata

**P0** - Provide a required reference transcript for scored runs. -
Allow a language/utterance label: Hindi, English, Hinglish/code-mixed,
or Mixed/Other. - Allow optional notes and scenario tags. - Allow
optional critical entities: - Person or organisation name - Location -
Date/time - Amount/currency - Numeric identifier or other custom field -
Provide a way to mark a test case as a starter example or user-created
case.

**Acceptance criteria** - A run without a reference transcript can still
show a transcript but must not show WER/CER as if scored. - The app
records whether reference text was manually entered, selected from a
starter suite, or imported.

### 7.4 STT provider integration

**P0** - Implement a server-side provider adapter interface. - Configure
the initial adapter for the available Gnani.ai STT API, using its
current official documentation and account-specific credentials. - Keep
API secrets in server-only environment variables. - Send audio through
the server or an approved provider flow; never expose secret keys to
client JavaScript. - Normalise provider responses into a stable internal
result shape. - Store provider status, request duration, error category,
model/deployment identifier when available, and a safe request
identifier if returned. - Provide timeouts, bounded retries for
retryable errors, and clear failure states. - Never retry
indefinitely. - Avoid logging raw audio, credentials, or full sensitive
transcripts by default.

**P0 fallback** - If credentials are absent, disable live execution with
a clear configuration message and provide fixture-based demo mode. -
Fixture results must be visibly marked as demo data and must not be
mixed into live metrics.

**P1** - Add a second provider adapter if time and API access allow. -
Add optional TTS playback only if it contributes to the demo and does
not distract from core evaluation.

**Acceptance criteria** - API calls are made only from trusted
server-side code. - Provider failures appear as failures, not fabricated
successful transcriptions. - A live result is labelled live only when a
real provider response was received.

### 7.5 Test conditions and audio transformations

**P0** - Provide a baseline run on the original audio. - Provide a small
set of transformations that can be performed reliably: - Add
configurable low-level background noise. - Adjust playback speed within
safe bounds. - Adjust volume/amplitude within safe bounds. - Clearly
label each transformed clip with its transformation and parameter
values. - Preserve the original clip and never overwrite it with
transformed audio. - Allow users to preview the transformed clip before
running it. - Make each API run a user-confirmed action.

**P1** - Add reverberation or room-like effects if implementation and
browser support are reliable. - Add an optional audio-normalisation
step, but ensure it is documented because it changes the input.

**Important limitations** - These are controlled, synthetic
transformations. They are not a substitute for recordings from real
mobile networks, actual noisy environments, or a representative field
dataset. - The UI must not call the test "real telephone network
simulation" unless such a test is actually implemented and validated. -
If a transformation cannot be applied to a given format reliably,
disable it and explain why rather than silently skipping it.

**Acceptance criteria** - Every challenged result is linked to the
original case and records the exact transformation configuration. -
Users can distinguish original audio, transformed audio, and demo
fixtures.

### 7.6 Evaluation engine

**P0** - Calculate word error rate (WER) from reference and hypothesis
using a documented tokenisation policy. - Calculate character error rate
(CER) as a secondary measure, with caveats for languages where
character-level comparison may not align with perceived quality. - Show
insertion, deletion, and substitution counts when available. - Highlight
differences between reference and hypothesis. - Compare baseline and
challenged runs. - Calculate critical-entity exact-match status for
user-specified entities. - Keep raw provider transcript and normalised
comparison text separately. - Document normalisation rules: Unicode
normalisation, whitespace handling, punctuation policy, case policy for
Latin text, and how Devanagari/Hinglish text is treated. - Do not
silently normalise away important digits or names.

**P1** - Add semantic or meaning-preservation review as an explicitly
experimental feature, not as ground truth. - Add user-editable
alias/normalisation rules for known spelling variants.

**Metric definitions** - WER = (substitutions + deletions + insertions)
/ number of words in the reference. - CER = (character substitutions +
deletions + insertions) / number of characters in the reference. -
Entity preservation = number of configured critical entities correctly
recovered / number of entities evaluated. If no entities are configured,
display "Not evaluated," not 100%. - Latency = elapsed time measured by
the application from request start to response completion. State whether
upload time is included. - Error delta = challenged run metric minus
baseline metric, with interpretation shown carefully because lower
WER/CER is better.

**Acceptance criteria** - The same reference and hypothesis produce the
same metrics on repeated calculations. - Empty reference text does not
result in division-by-zero or a misleading zero-error score. - When no
reference transcript is present, score cards are replaced with
"Reference transcript required." - The method used to calculate every
displayed metric is accessible from the UI.

### 7.7 Critical-detail preservation

**P0** - Let users define a list of critical values before the run. -
Compare each value with the transcription using a documented,
conservative matching rule. - Display "matched," "not found," or "needs
review." - Avoid assuming that fuzzy matches are definitely correct. -
Highlight high-impact discrepancies, especially dates, amounts, and
numeric identifiers.

**Acceptance criteria** - Missing entities are not reported as
preserved. - The app distinguishes exact matches from fuzzy or
manual-review outcomes. - The feature is described as a heuristic, not a
guarantee of semantic understanding.

### 7.8 Results dashboard

**P0** Show: - Test name and timestamp - Live provider run or demo
fixture label - Language label - Original versus transformed condition -
Reference transcript - Actual transcript - WER and CER when scorable -
Critical-entity results - Measured latency - Provider status and error
details - Transcript diff - Test configuration - Limitations and caveats

**P1** - Trend charts across repeated runs. - Filter by language,
condition, status, and provider. - Small test-run comparison table.

**Acceptance criteria** - Every metric can be traced to a specific test
run. - Demo data is visually distinct from live results. - A failed API
call is never displayed as a successful zero-WER result.

### 7.9 Starter test suite

**P0** - Include a small, manually reviewed set of example phrases
across Hindi, English, and Hinglish. - Include representative categories
such as: - Names and locations - Dates and appointments - Currency and
quantities - Common code-switching patterns - Fast but intelligible
speech - Similar-sounding words where a reference can be established -
Include reference text and optional critical entities. - Mark all
starter data as illustrative, not a representative national benchmark. -
Use recordings with permission or record original sample utterances with
informed consent.

**P1** - Allow users to create and save their own test cases locally or
in their account, depending on the implemented persistence model. - Add
more languages only after test content and transcription review are
available.

**Acceptance criteria** - Every starter case has a reference transcript
reviewed by a human. - Do not use a generated transcript as the
unquestioned ground truth. - The dataset description states its size,
language coverage, and limitations.

### 7.10 Test history and export

**P0** - Maintain a run history for the current browser session or local
workspace. - Export results as JSON and CSV. - Provide a print-friendly
report page suitable for Save as PDF. - Include a methodology and
limitations section in the export.

**P1** - Persist cases and results in a database for signed-in users. -
Add shareable, read-only reports with explicit consent and expiration.

**Acceptance criteria** - Exported results include enough metadata to
reproduce the test setup. - Exports exclude raw audio by default. - Any
share feature is opt-in and never makes a recording public by default.

------------------------------------------------------------------------

## 8. Information Architecture and Screens

### 8.1 Public landing page

-   Hero: "Your voice AI has been tested in a lab. Has it survived
    Bharat?"
-   Supporting copy explaining the tool without claiming national-scale
    validation.
-   Primary CTA: "Run a Crash Test"
-   Secondary CTA: "Explore Demo"
-   Three steps: Capture → Stress → Inspect
-   Example result card labelled "Illustrative demo"
-   Supported dimensions and limitations
-   Footer with privacy, methodology, and project details

### 8.2 Workspace dashboard

-   Summary cards: Test cases, runs completed, live runs, failed runs.
-   Recent test runs.
-   Quick-start buttons.
-   Prominent notice when using demo mode.
-   Do not show aggregate quality statistics until there is enough real,
    comparable data.

### 8.3 Test Lab

Suggested layout: - Left panel: audio recorder/uploader and playback. -
Centre panel: reference transcript and critical entities. - Right panel:
language, condition, and provider options. - Main action: "Run Baseline"
or "Run Crash Test." - Usage notice showing that a live provider call
may consume account credits.

### 8.4 Run results

-   Top status row: Success / Provider error / Demo fixture.
-   Transcript comparison view.
-   Metric cards.
-   Critical-detail table.
-   Baseline-versus-challenged comparison.
-   Transformation details.
-   Export button.
-   "What this result does and does not mean" explanation.

### 8.5 Test suite page

-   Starter cases grouped by language and scenario.
-   Search/filter.
-   Case detail preview.
-   Select one or a small number of cases for a run.
-   Confirm before batch execution because each case may consume
    provider credits.

### 8.6 Methodology page

Must explain: - WER/CER definitions and tokenisation. - How critical
entities are checked. - How audio transformations work. - Difference
between demo fixtures and live provider results. - Dataset size and
provenance. - Known limitations. - How users can report a metric or
test-case issue.

------------------------------------------------------------------------

## 9. UX and Visual Design Direction

### Desired feeling

A premium developer tool that feels like a **flight-test console or
diagnostic lab**, not a generic admin template.

### Visual direction

-   Dark graphite or near-black workspace with high-contrast readable
    text.
-   One vivid accent colour used for primary actions and charts.
-   Clear semantic states: success, warning, failure, informational.
-   Monospaced typography for transcripts, metrics, run IDs, and
    configuration details where useful.
-   Subtle motion only for recording state, run progress, and result
    transitions.
-   Use accessible contrast and avoid colour as the only signal.
-   Responsive layout: desktop-first for analysis, usable on mobile for
    recording and reviewing results.
-   Charts should communicate real data only; no decorative fake graphs.

### Signature interaction

A **Crash Test Run** animation: 1. "Preparing audio" 2. "Applying
selected condition" (only when a transformation actually occurs) 3.
"Sending to speech engine" 4. "Comparing transcript" 5. "Report ready"

The animation must reflect actual backend status. Never display fake
progress stages after the operation has already failed.

### Copy tone

Confident, technical, and approachable. Avoid claims such as "100%
accurate," "certified safe," or "works for every Indian accent."

------------------------------------------------------------------------

## 10. Technical Architecture

### 10.1 Proposed stack

**Frontend and server** - Next.js with App Router - React - TypeScript
with strict mode - Tailwind CSS - A maintained accessible component
library, such as shadcn/ui, where useful - Zod for request and
environment validation - React Hook Form for complex forms if needed

**Audio** - Browser MediaRecorder API for capture - Web Audio API for
client-side playback and supported transformations - A small, tested
audio-processing utility layer - Avoid introducing a heavy waveform or
audio-processing dependency unless it materially improves the MVP

**Backend** - Next.js Route Handlers for MVP API endpoints - Provider
adapter service for STT - Evaluation module for WER/CER and entity
matching - Server-side request validation, size limits, timeouts, and
rate limiting

**Persistence** - MVP option A: browser-local history for a single-user
demo. - MVP option B: managed Postgres/Supabase if durable cross-session
history is required and setup time permits. - Choose one persistence
approach early; do not build both in the MVP. - Store audio only when
required and only with explicit consent. Prefer transient processing and
short retention.

**Testing** - Vitest for unit tests - Playwright for critical end-to-end
flows - TypeScript, ESLint, formatting, and production build checks in
CI

**Deployment** - Deploy the Next.js application to a suitable managed
host. - Keep provider keys in server-side deployment environment
variables. - Set upload limits and request timeouts compatible with the
host. - Verify provider terms, data processing conditions, and regional
requirements before sending user audio.

Exact package versions must be selected at implementation time from
current stable releases. Do not assume a version from this PRD is the
latest.

### 10.2 Logical architecture

``` text
Browser UI
  ├── Microphone / file input
  ├── Audio preview and optional transformations
  ├── Reference transcript and entity form
  └── Results / comparison / export
          |
          v
Next.js Route Handlers
  ├── Validate request and file
  ├── Enforce limits and rate controls
  ├── Create run metadata
  ├── Call STT Provider Adapter
  ├── Normalise provider response
  └── Return structured result
          |
          +--------------------+
          |                    |
          v                    v
Gnani.ai STT API          Evaluation Engine
(real API response)       (WER / CER / entities)
          |                    |
          +----------+---------+
                     v
              Run Result Model
                     |
                     v
          UI / history / export
```

### 10.3 Provider adapter contract

Define a provider-neutral interface conceptually equivalent to:

``` ts
type TranscriptionRequest = {
  audio: File | Blob;
  languageHint?: string;
  requestId: string;
};

type TranscriptionResult = {
  text: string;
  provider: string;
  model?: string;
  durationMs: number;
  providerRequestId?: string;
  status: "success";
  metadata?: Record<string, unknown>;
};

interface SpeechToTextProvider {
  transcribe(input: TranscriptionRequest): Promise<TranscriptionResult>;
}
```

Implementation notes: - Adjust the contract to the actual provider API
rather than assuming the API supports these exact fields. - Keep
provider-specific parsing inside the adapter. - Validate provider
responses at runtime. - Do not pass arbitrary untrusted metadata into
the UI. - Never return secrets or internal stack traces to the client.

### 10.4 Suggested API routes

Route names are proposals and may be refined during implementation.

-   `POST /api/transcriptions` --- execute one real transcription.
-   `POST /api/evaluations` --- score a reference/hypothesis pair or
    return a validated score.
-   `POST /api/test-runs` --- create a run record and orchestrate the
    workflow if needed.
-   `GET /api/test-runs` --- retrieve run history if persistence is
    implemented.
-   `GET /api/test-runs/[id]` --- retrieve one run.
-   `DELETE /api/test-runs/[id]` --- delete a stored run and associated
    audio where applicable.
-   `GET /api/health` --- basic service health, excluding secret values.

Do not create a complex endpoint for every UI component. Keep business
logic in tested service modules and keep route handlers thin.

------------------------------------------------------------------------

## 11. Data Model

The final database choice may be deferred, but the domain model should
be stable.

### TestCase

-   `id`
-   `title`
-   `languageLabel`
-   `referenceTranscript`
-   `criticalEntities[]`
-   `tags[]`
-   `sourceType` (starter/user)
-   `createdAt`
-   `updatedAt`

### AudioAsset

-   `id`
-   `testCaseId`
-   `storageMode` (transient/local/managed)
-   `mimeType`
-   `durationMs`
-   `sizeBytes`
-   `checksum` where useful
-   `createdAt`
-   `expiresAt` if stored
-   No public URL by default

### TestRun

-   `id`
-   `testCaseId`
-   `status` (queued/running/succeeded/failed/demo)
-   `mode` (live/demo)
-   `provider`
-   `model`
-   `conditionType` (baseline/noise/speed/volume/other)
-   `conditionConfig`
-   `hypothesisTranscript`
-   `wer`
-   `cer`
-   `substitutions`
-   `deletions`
-   `insertions`
-   `entityResults[]`
-   `latencyMs`
-   `errorCode`
-   `providerRequestId`
-   `createdAt`
-   `completedAt`
-   `evaluationVersion`

### Design rules

-   Do not store API secrets in application data.
-   Do not store raw audio permanently by default.
-   Use an explicit retention policy for any server-side audio.
-   Keep demo fixtures separate from live run records or give them an
    unmistakable `mode: demo` field.
-   Use a version identifier for metric/tokenisation logic so future
    changes do not silently alter historical scores.

------------------------------------------------------------------------

## 12. Evaluation and Benchmark Methodology

### 12.1 Reference transcript quality

A metric is only as reliable as its reference. Starter transcripts
should be reviewed by a fluent human familiar with the utterance
language. For code-mixed speech, preserve the spoken words rather than
forcing everything into one script unless the test explicitly evaluates
transliteration.

### 12.2 Text normalisation

Document a conservative normalisation policy: - Unicode normalisation. -
Collapse repeated whitespace. - Apply punctuation normalisation only
where the chosen metric policy specifies it. - Do not silently convert
or remove dates, numbers, currency values, names, or language-specific
distinctions. - Preserve both original strings and normalised strings
for inspection. - Report the policy version with each run.

### 12.3 Aggregate scores

For MVP, prioritise per-case results and small-suite comparisons. If
aggregate metrics are shown: - State the number of test cases. - State
the language and condition mix. - Use comparable reference transcripts
and consistent tokenisation. - Avoid presenting a tiny convenience
sample as a national benchmark. - Avoid comparing different provider
models without disclosing configuration differences.

### 12.4 Simulated condition comparison

The app may report that a particular transformed clip produced a higher
WER than the baseline. It may not conclude that all real-world noisy
calls will have the same degradation. Phrase findings narrowly,
e.g. "WER increased by X percentage points on this transformed clip
under these settings."

### 12.5 Meaning and entity checks

Critical-entity checks are useful for finding high-impact errors but are
not a complete semantic understanding metric. If fuzzy matching is
added, show its threshold and label the result as "possible match" or
"needs review."

------------------------------------------------------------------------

## 13. Privacy, Security, and Responsible Use

### Required safeguards

-   Microphone access only after an explicit user action and browser
    permission.
-   Clear notice before audio is sent to a third-party provider.
-   Never put provider API keys in client-side code or `NEXT_PUBLIC_`
    variables.
-   Server-side input validation and strict file-size/duration limits.
-   Use secure transport in production.
-   Do not log raw audio or full transcripts by default.
-   Avoid collecting unnecessary personal information.
-   Provide delete controls for persisted runs and audio.
-   Use non-public storage by default; signed, short-lived URLs if
    storage is necessary.
-   Rate-limit endpoints and constrain concurrency to prevent accidental
    credit exhaustion.
-   Do not automatically launch large batch jobs.
-   Use only recordings for which the user has appropriate permission.
-   Do not upload confidential, medical, financial, or other sensitive
    recordings in the challenge demo.
-   Avoid recording bystanders without their consent.
-   Review the provider's terms, privacy policy, retention practices,
    and permitted use before sending audio.

### Threats to consider

-   Exposed API keys.
-   Maliciously large or malformed uploads.
-   API credit abuse.
-   Cross-user access to another user's recordings or reports if
    accounts are introduced.
-   Unintended audio retention.
-   Transcript content leaking into application logs.
-   Fake demo results being mistaken for live results.

### MVP privacy decision

Prefer transient server processing and local browser history unless
persistent history is essential. If a database or object store is
introduced, document retention and deletion behaviour before launch.

------------------------------------------------------------------------

## 14. Performance and Reliability Requirements

These are initial engineering targets, not claims about provider
performance.

-   The landing page should feel responsive on a normal broadband
    connection.
-   The app should show a clear loading state immediately after a run
    begins.
-   Client-side metric calculation should complete quickly for short
    transcripts.
-   Set a configurable maximum audio duration and upload size.
-   Use bounded API timeouts and retries.
-   Return structured error messages for provider timeout, rate limit,
    invalid audio, missing credentials, and unknown provider errors.
-   Do not block the whole UI while a report is being prepared.
-   Handle refresh/navigation without corrupting a completed run;
    durable recovery depends on the selected persistence option.
-   Ensure keyboard-accessible controls and visible focus states.
-   Provide readable contrast, labels, and error announcements.

Do not promise a fixed transcription latency before measuring the
configured provider in the actual deployment environment.

------------------------------------------------------------------------

## 15. Analytics and Success Metrics

### Product success for the challenge demo

-   A first-time user can complete a baseline test without assistance.
-   At least one end-to-end live provider test succeeds in the final
    demo environment, if credentials and service access are available.
-   At least one test demonstrates a measurable difference between
    baseline and a transformed condition, without implying universal
    conclusions.
-   Every displayed metric can be reproduced from the underlying
    reference and output.
-   Demo fixtures and live results are clearly distinguished.
-   The demo can be completed within approximately 2--3 minutes.
-   The user can export a report.

### Product analytics (if implemented)

Collect minimal, non-sensitive events: - `test_created` -
`audio_selected` - `transcription_started` - `transcription_succeeded` -
`transcription_failed` - `report_exported`

Do not send transcript text or raw audio to analytics. Analytics are
optional and lower priority than core testing.

### Do not optimise for

-   Number of API calls.
-   A high accuracy score achieved by cherry-picking examples.
-   An impressive-looking dashboard without valid data.
-   Claims about all Indian languages based on a small test suite.

------------------------------------------------------------------------

## 16. MVP Scope and Delivery Plan

The challenge deadline is close. Prioritise one complete, reliable path
over breadth.

### Phase 0 --- Verify access and reduce risk

-   Confirm access to the current Gnani.ai STT API documentation.
-   Confirm credentials, endpoint, authentication method, supported
    audio formats, language behaviour, request limits, and response
    schema.
-   Run one small manual API request outside the UI.
-   Confirm the remaining programme credits and avoid unnecessary calls.
-   Decide whether audio processing happens in-browser or server-side.
-   Decide whether MVP history is local-only or database-backed.

**Exit criteria:** one verified provider request or a documented
demo-only fallback.

### Phase 1 --- Product skeleton

-   Set up Next.js App Router and TypeScript.
-   Create the visual shell and navigation.
-   Build landing page, test lab, and results layout.
-   Add demo fixtures with unmistakable labels.
-   Add form validation and responsive states.

**Exit criteria:** a complete clickable flow exists without live API
integration.

### Phase 2 --- Core testing workflow

-   Implement audio recording/upload and preview.
-   Implement reference transcript and critical entity inputs.
-   Implement provider adapter and server-side transcription endpoint.
-   Implement WER/CER and diff rendering.
-   Add error handling and usage confirmation before live calls.

**Exit criteria:** a live transcription can be scored end-to-end.

### Phase 3 --- Crash tests

-   Implement baseline and one or two reliable audio transformations.
-   Preview transformed audio.
-   Record transformation metadata.
-   Run transformed variants and compare metrics.
-   Ensure a failed transformation cannot silently be treated as a valid
    test.

**Exit criteria:** one original clip can be compared with at least one
transformed variant.

### Phase 4 --- Reporting and polish

-   Add starter test cases.
-   Add run history appropriate to the chosen persistence model.
-   Add JSON/CSV export and print-friendly report.
-   Add methodology, privacy, and limitations pages.
-   Add responsive and accessibility checks.

**Exit criteria:** a judge can complete and understand the entire demo.

### Phase 5 --- Release hardening

-   Run unit tests for metric logic.
-   Run end-to-end tests for the main journey.
-   Verify server-only secret handling.
-   Test missing key, invalid file, timeout, rate limit, and provider
    error states.
-   Test deployment environment variables.
-   Record a fallback demo path in case the provider API is unavailable
    during judging.

**Exit criteria:** the app deploys reliably and has a credible live/demo
fallback.

### Suggested day-by-day schedule

  -----------------------------------------------------------------------
  Date                    Focus                   Deliverable
  ----------------------- ----------------------- -----------------------
  Oct 28                  Lock scope, verify API  Technical spike and
                          and credits             final MVP decisions

  Oct 29                  Next.js setup and       App shell and landing
                          design system           page

  Oct 30                  Audio capture/upload    Usable Test Lab
                          and test form           

  Oct 31                  Provider adapter and    Live STT call
                          route handler           

  Nov 1                   Metrics, transcript     Scored result page
                          diff, entity checks     

  Nov 2                   Audio transformations   Baseline/challenge
                                                  comparison

  Nov 3                   Starter suite and test  Repeatable test cases
                          history                 

  Nov 4                   Export and methodology  Report workflow

  Nov 5                   UI polish and           Demo-quality interface
                          accessibility           

  Nov 6                   Automated testing and   Stable candidate
                          edge cases              

  Nov 7                   Deploy and test real    Public demo URL
                          environment             

  Nov 8                   Demo script and backup  Recorded walkthrough
                          mode                    

  Nov 9                   Bug fixes and freeze    Submission-ready
                                                  release

  Nov 10                  Challenge deadline      Submit and present
  -----------------------------------------------------------------------

This is a planning target, not a guarantee. If provider access is
blocked, prioritise a polished, honest demo mode and a functioning local
evaluation engine rather than spending the entire schedule on an
undocumented integration.

------------------------------------------------------------------------

## 17. Acceptance Criteria for MVP Release

The MVP is considered complete when all P0 criteria below pass:

1.  Landing page clearly explains the product and its limitations.
2.  User can record or upload a short clip and play it back.
3.  User can enter a reference transcript and optional critical
    entities.
4.  User can run a live transcription when valid provider credentials
    are configured.
5.  Missing credentials produce a clear configuration state, not a fake
    success.
6.  Demo fixtures are visibly labelled and excluded from live metrics.
7.  WER/CER calculations are unit-tested against known examples.
8.  The result page shows reference and hypothesis side by side.
9.  At least one supported transformation can be previewed and
    evaluated.
10. Baseline and transformed runs can be compared.
11. A report can be exported as JSON or CSV.
12. No provider secret is exposed in client bundles or browser network
    responses.
13. File size, duration, and request limits are enforced.
14. API errors and unsupported formats have understandable UI states.
15. The deployed app has a demo path that works if live provider access
    fails.
16. Methodology and limitations are available from the UI.

------------------------------------------------------------------------

## 18. Risks and Mitigations

  -----------------------------------------------------------------------
  Risk                    Impact                  Mitigation
  ----------------------- ----------------------- -----------------------
  Provider API access or  Live STT integration    Verify API first; build
  documentation is        delayed                 adapter boundary and
  unavailable                                     clearly labelled
                                                  fixtures

  API credits are limited Cost and demo risk      Confirm before calls;
                                                  require user
                                                  confirmation; cap batch
                                                  size; cache only where
                                                  appropriate and
                                                  permitted

  Audio format mismatch   Tests fail unexpectedly Validate formats and
                                                  use a documented
                                                  conversion path only if
                                                  necessary

  Synthetic noise has     Misleading conclusions  Label transformations
  unrealistic effects                             as synthetic and avoid
                                                  claims about real calls

  Reference transcript is Invalid metric          Human-review starter
  wrong                                           references and preserve
                                                  source/provenance

  Hinglish tokenisation   Scores may be hard to   Document normalisation
  varies                  interpret               and display transcript
                                                  diff alongside scores

  Scope expands           Deadline missed         Treat real-time
                                                  conversation, accounts,
                                                  leaderboards, and
                                                  multiple providers as
                                                  post-MVP

  UI metrics look         Trust lost              Unit-test formulas and
  impressive but are                              trace each metric to a
  invalid                                         real run

  Audio contains          Privacy risk            Consent notice, minimal
  sensitive information                           retention, delete
                                                  controls, no sensitive
                                                  demo recordings

  Deployment environment  Demo failure            Deploy early and keep a
  differs from local                              tested fixture mode
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 19. Demo Script (2--3 Minutes)

1.  **Open with the problem:** "A voice system can understand the
    general sentence and still get the amount or date wrong."
2.  Open a labelled Hinglish test case with a human-reviewed reference
    transcript.
3.  Run the baseline transcription using the live provider if available.
4.  Show the actual transcript, WER, and critical-entity status.
5.  Apply one controlled transformation, such as mild synthetic
    background noise, and preview it.
6.  Run the transformed version.
7.  Compare the two outputs and show the exact transcript differences.
8.  Explain the result narrowly: "On this test clip and these settings,
    the output changed this way."
9.  Open the methodology note to show how metrics are calculated and why
    synthetic noise is not the same as real telephony audio.
10. Export the report.
11. If live API access is unavailable during judging, switch to a
    clearly labelled fixture and explain that the fixture demonstrates
    the interface while live runs require provider credentials.

### Demo rule

Never rehearse a claim that depends on a result that has not actually
been observed. Select the final demo example after testing the provider
and transformation in the deployed environment.

------------------------------------------------------------------------

## 20. Post-MVP Roadmap

### V1.1 --- Better regression testing

-   Durable test suites and repeatable runs.
-   Versioned configurations.
-   Run-to-run regression alerts.
-   Optional comparison between supported providers.

### V1.2 --- More realistic acoustic tests

-   Validated room impulse responses and additional controlled acoustic
    conditions.
-   Optional field-recording dataset with consent and metadata.
-   More rigorous audio-quality diagnostics.

### V1.3 --- Expanded Indian language coverage

-   Additional language labels and reviewed reference data.
-   Support for script variants and transliteration policies.
-   Evaluation by language and scenario, with sample sizes disclosed.

### V2 --- Voice-agent evaluation

-   Evaluate multi-turn conversations, interruptions, response
    correctness, and task completion.
-   Test agent behaviour using a controlled scenario harness.
-   Separate speech recognition quality from reasoning and
    dialogue-policy quality.

These are future directions, not MVP commitments.

------------------------------------------------------------------------

## 21. Open Questions and Decisions to Resolve Before Coding

1.  What exact Gnani.ai STT endpoint, authentication method, and payload
    format are available to this challenge account?
2.  Which audio formats and maximum duration does the endpoint accept?
3.  Does the API require an explicit language parameter, or does it
    support automatic language identification?
4.  What response fields are available for model name, latency,
    confidence, and request ID?
5.  What are the remaining credit balance, per-request costs, and rate
    limits?
6.  Does provider policy permit temporary processing of user-recorded
    test clips, and what retention applies?
7.  Is local-only history sufficient for the judging demo, or is durable
    database persistence necessary?
8.  Which languages can the team confidently review for
    reference-transcript quality?
9.  Which audio transformations are reliable in the target browsers?
10. What is the final deployment target and its upload/timeout limit?

**Rule:** do not guess the provider API contract. Verify it against
current official documentation and the actual account before
implementing the adapter.

------------------------------------------------------------------------

## 22. Instructions for the AI Coding Agent

Treat this PRD as the product contract. Before writing substantial code:

1.  Inspect the repository and report existing framework, package
    manager, scripts, and structure.
2.  Read current official documentation for Next.js and any library
    whose APIs are version-sensitive.
3.  Verify the actual Gnani.ai STT API contract from official
    documentation or supplied account materials. Do not invent
    endpoints, headers, request fields, or response schemas.
4.  Propose a concise implementation plan with milestones and risks.
5.  Create a task checklist aligned to P0/P1 priorities.
6.  Implement the smallest complete vertical slice first: audio input →
    server-side STT → reference comparison → results.
7.  Use strict TypeScript and runtime validation at external boundaries.
8.  Write unit tests for metric calculations before building elaborate
    charts.
9.  Keep secrets server-only and provide an `.env.example` with
    placeholder names, never real credentials.
10. Clearly separate live provider results from demo fixtures in types,
    UI, storage, and exports.
11. Do not fabricate API responses, test results, confidence values, or
    benchmarks.
12. Do not add a database, authentication, queue, or third-party service
    unless the selected MVP scope requires it.
13. Run linting, type checking, unit tests, and a production build.
    Report the actual results; do not claim checks passed unless they
    ran successfully.
14. Update project documentation with setup, environment variables,
    provider configuration, test commands, deployment steps, and
    limitations.
15. If a required credential or API detail is missing, continue with
    independently buildable work and clearly identify the blocker rather
    than guessing.

### Required implementation deliverables

-   Working Next.js application.
-   Clean, responsive interface.
-   Server-side STT provider adapter.
-   Audio capture/upload and preview.
-   Text evaluation module with unit tests.
-   Baseline-versus-transformed comparison.
-   Demo fixture mode clearly labelled.
-   Exportable report.
-   `.env.example`.
-   `README.md` with local setup and deployment.
-   Methodology, privacy, and limitations documentation.
-   A short manual QA checklist and known-issues list.

------------------------------------------------------------------------

## 23. Final Product Definition

**Bharat Voice Crash Test is a browser-based, evidence-first test lab
for evaluating speech recognition on Indian-language and code-mixed
utterances under controlled audio conditions.** It lets a user supply a
reference transcript, run a real speech-to-text provider, inspect word
and character errors, check critical details, apply clearly labelled
audio transformations, and export a reproducible report.

The MVP succeeds if it proves one thing convincingly:

> **A voice AI should not just sound impressive. Its failures should be
> measurable, explainable, and reproducible.**

Build the smallest real version of that promise first.
