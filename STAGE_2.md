# STAGE 2: AI-Powered Due Diligence Analysis - Complete Beginner's Guide

**Status**: ✅ Complete Implementation  
**Date**: March 24, 2026  
**Project**: Housing Investment Analysis Platform (Backend)  
**Prerequisites**: Completed STAGE_1.md

---

## Table of Contents

1. [What is Stage 2?](#what-is-stage-2)
2. [Prerequisites You Need](#prerequisites-you-need)
3. [Understanding Async Architecture](#understanding-async-architecture)
4. [Project Updates (From Stage 1)](#project-updates-from-stage-1)
5. [Building Each New Component](#building-each-new-component)
6. [Testing the Analysis Pipeline](#testing-the-analysis-pipeline)
7. [Running with Docker](#running-with-docker)
8. [Glossary of Technical Terms](#glossary-of-technical-terms)

---

## What is Stage 2?

### Simple Explanation

Imagine you just extracted text from a real estate document in Stage 1. Now in Stage 2, we want to **analyze** that text using AI to answer important questions:

- **Legal**: Are there legal risks in this property?
- **Financial**: What's the risk level of investing?
- **Valuation**: What is the property worth?
- **Decision**: Should we invest or not?

Instead of doing this analysis immediately (which could take 30+ seconds and freeze the user), we do it **in the background** while the user gets an immediate response.

### Real-World Analogy

**Stage 1**: You scan a document and copy important information  
**Stage 2**: You hire 3 specialists to analyze that information:

- A lawyer analyzes legal risks
- A accountant analyzes financial value
- A real estate expert analyzes property quality
- A manager reviews everything and makes final decision

All 3 work at the **same time** (in parallel), then report back when done.

### What's Different From Stage 1?

| Aspect           | Stage 1                                        | Stage 2                                               |
| ---------------- | ---------------------------------------------- | ----------------------------------------------------- |
| **Speed**        | Document uploaded → Text extracted immediately | Request submitted → Analysis queued → Done when ready |
| **Process**      | Synchronous (waits for result)                 | Asynchronous (doesn't wait)                           |
| **Tech Stack**   | FastAPI only                                   | FastAPI + Celery + Redis                              |
| **Intelligence** | Rule-based validation                          | OpenAI AI models                                      |
| **Duration**     | 1-5 seconds                                    | 30-120 seconds (runs in background)                   |

---

## Prerequisites You Need

### New Tools Required (Beyond Stage 1)

#### 1. Redis (Message Queue)

**What it is**: An in-memory storage system that acts like a mailbox for tasks  
**Why we need it**: To store analysis jobs and their results  
**How to install**:

- On macOS: `brew install redis`
- On Windows: Download from https://github.com/microsoftarchive/redis/releases
- On Linux: `sudo apt-get install redis-server`

**Check if installed**:

```bash
redis-cli --version
# Should show version number
```

#### 2. OpenAI API Key

**What it is**: Authentication token to use OpenAI's GPT models  
**Why we need it**: To run AI analysis on documents  
**How to get**:

1. Go to https://platform.openai.com
2. Sign up or log in
3. Go to API Keys: https://platform.openai.com/api-keys
4. Create a new secret key
5. **Copy and save it** (you'll only see it once!)

#### 3. Understanding of Async Programming (Conceptual)

**What it is**: Code that doesn't wait for long tasks to finish  
**Why we need it**: Analysis takes time; we don't want users to wait

### Verify Prerequisites

Run these commands:

```bash
# Check PostgreSQL
psql --version

# Check Python
python3 --version

# Check Redis
redis-cli --version

# Activate virtual environment
source venv/bin/activate
```

All should work from Stage 1!

---

## Understanding Async Architecture

### The Problem with Synchronous (Stage 1 Style)

```
User uploads document
    ↓
FastAPI processes immediately:
    - Save file ✓ (fast, 1 second)
    - Extract text ✓ (medium, 3 seconds)
    - User gets response after 4 seconds

If we add analysis:
    - Save file ✓ (1 second)
    - Extract text ✓ (3 seconds)
    - RUN AI ANALYSIS ✗ (60 seconds)
    - User waits 64 seconds...
```

**Problem**: User loses patience. Browser times out. Service looks frozen.

### The Solution: Asynchronous (Stage 2 Style)

```
User uploads document
    ↓
FastAPI processes quickly:
    - Save file ✓ (1 second)
    - Extract text ✓ (3 seconds)
    - **Queue analysis job** ✓ (0.1 seconds)
    - Return immediately: "Job #123 queued" ✓
    ↓
User gets response in 4.1 seconds!
    ↓
Meanwhile, in the background:
    - Redis stores job #123
    - Celery worker picks it up
    - Worker runs OpenAI analysis (60 seconds)
    - Worker saves results
    ↓
User polls: "Is job #123 done?"
    - First poll (5 seconds): "Still processing"
    - Later poll (65 seconds): "Done! Here are results"
```

**Solution**: User doesn't wait. Service is responsive.

### Key Concept: The Queue

```
FastAPI (Web Server)
    ↓ (enqueues job)
Redis (Message Queue)
    ↓ (worker picks up)
Celery Worker (Background Process)
    ↓ (does slow work)
PostgreSQL (Stores results)
```

Think of it like:

- **FastAPI** = Customer at restaurant counter
- **Redis** = Kitchen order ticket system
- **Celery** = Chef cooking in kitchen
- **PostgreSQL** = Restaurant's order history

Customer orders, gets ticket number, comes back later to pick up food.

---

## Project Updates (From Stage 1)

### What Stays the Same

All Stage 1 components work unchanged:

- ✅ Document upload
- ✅ Text extraction
- ✅ Text validation
- ✅ File storage
- ✅ FAISS vector search
- ✅ Most of `main.py` endpoints

### What's New

| File                                | Purpose                    | New/Modified |
| ----------------------------------- | -------------------------- | ------------ |
| `celery_app.py`                     | Celery configuration       | **NEW**      |
| `worker.py`                         | Worker process entry point | **NEW**      |
| `services/analysis_tasks.py`        | Async task pipeline        | **NEW**      |
| `services/analysis_intelligence.py` | OpenAI integrations        | **NEW**      |
| `services/regulation_retrieval.py`  | Regulation corpus search   | **NEW**      |
| `main.py`                           | Add 2 analysis endpoints   | **MODIFIED** |
| `models.py`                         | Add analysis data models   | **MODIFIED** |
| `docker-compose.yml`                | Add Redis + Worker         | **MODIFIED** |
| `requirements.txt`                  | Add Celery, Redis, OpenAI  | **MODIFIED** |

### New Database Tables

```sql
-- Tracks analysis jobs
CREATE TABLE analyses (
    id INTEGER PRIMARY KEY,
    document_id INTEGER,
    status VARCHAR(20),  -- queued, processing, done, failed
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    error TEXT,
    model_version VARCHAR(50)
);

-- Stores AI analysis outputs
CREATE TABLE analysis_outputs (
    analysis_id INTEGER PRIMARY KEY,
    legal_json TEXT,        -- Legal analysis result
    risk_json TEXT,         -- Risk analysis result
    valuation_json TEXT,    -- Valuation analysis result
    final_json TEXT         -- Final synthesis result
);

-- Event log for debugging
CREATE TABLE analysis_events (
    id INTEGER PRIMARY KEY,
    analysis_id INTEGER,
    stage VARCHAR(50),      -- which analysis stage
    timestamp TIMESTAMP,
    payload TEXT
);
```

---

## Building Each New Component

### Component 1: Celery Configuration (celery_app.py)

**What it does**: Configures how Celery connects to Redis  
**Why we need it**: Tells Celery where the Redis queue is

Create `celery_app.py`:

```python
"""
Celery application configuration for asynchronous analysis tasks.
Connects FastAPI to background workers via Redis.
"""
from celery import Celery
from config import settings

# Create Celery app instance
celery_app = Celery(
    "document_analysis",
    broker=settings.CELERY_BROKER_URL,      # Redis connection for tasks
    backend=settings.CELERY_RESULT_BACKEND, # Redis connection for results
)

# Configure Celery behavior
celery_app.conf.update(
    task_serializer="json",           # Convert tasks to JSON for storage
    result_serializer="json",         # Store results as JSON
    accept_content=["json"],          # Accept JSON format
    timezone="UTC",                   # Use UTC time
    enable_utc=True,                  # Store times in UTC
    task_track_started=True,          # Track when task starts
)
```

**Key Concepts**:

- **Broker**: The message queue (Redis) where tasks wait
- **Backend**: Where results are stored (also Redis)
- **Serializer**: Format for storing tasks (JSON is human-readable)

### Component 2: Analysis Models Update (models.py)

Add these models to your existing `models.py`:

```python
# ============================================================================
# SQLAlchemy ORM Models for Analysis
# ============================================================================

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON

class Analysis(Base):
    """
    Represents an analysis job for a document.
    Tracks the status and timing of AI analysis.
    """
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)

    # Job status: queued, processing, done, failed
    status = Column(String(20), default="queued", nullable=False)

    # Timestamps
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    # Error tracking
    error = Column(Text, nullable=True)  # Error message if failed

    # Model version for reproducibility
    model_version = Column(String(50), default="gpt-4", nullable=False)

    # Created timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AnalysisOutput(Base):
    """
    Stores the AI analysis results for each module.
    Each module produces JSON output.
    """
    __tablename__ = "analysis_outputs"

    analysis_id = Column(Integer, ForeignKey("analyses.id"), primary_key=True)

    # Each module produces JSON result
    legal_json = Column(Text, nullable=True)          # Legal risks
    risk_json = Column(Text, nullable=True)           # Financial risks
    valuation_json = Column(Text, nullable=True)      # Property valuation
    final_json = Column(Text, nullable=True)          # Final decision


class AnalysisEvent(Base):
    """
    Event log for analysis jobs.
    Useful for debugging and understanding the analysis flow.
    """
    __tablename__ = "analysis_events"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)

    # Which stage (legal, risk, valuation, synthesis, etc)
    stage = Column(String(50), nullable=False)

    # When this event occurred
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Event data (serialized JSON)
    payload = Column(Text, nullable=True)


# ============================================================================
# Pydantic Schemas for API
# ============================================================================

class AnalyzeRequest(BaseModel):
    """Request to start an analysis."""
    document_id: int = Field(..., description="ID of document to analyze")


class AnalyzeCreateResponse(BaseModel):
    """Response when analysis job is created."""
    analysis_id: int
    document_id: int
    status: str = "queued"
    message: str


class AnalysisStatusResponse(BaseModel):
    """Response for analysis status query."""
    analysis_id: int
    document_id: int
    status: str  # queued, processing, done, failed
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error: Optional[str] = None


class AnalysisOutputResponse(BaseModel):
    """Response with analysis results."""
    analysis_id: int
    status: str
    outputs: Optional[dict] = None  # Parsed JSON from modules
    error: Optional[str] = None


class AnalysisResultPayload(BaseModel):
    """Single module analysis result."""
    module_name: str
    findings: str
    recommendations: list[str]
    confidence_score: float
```

**Key Concepts**:

- **Status**: Job can be in different states (queued, processing, done, failed)
- **Timestamps**: When job started and finished (for tracking)
- **Outputs**: Each module produces its own JSON result
- **Events**: Log of what happened (for debugging)

### Component 3: Analysis Intelligence (services/analysis_intelligence.py)

This service calls OpenAI to analyze documents.

Create `services/analysis_intelligence.py`:

```python
"""
AI intelligence layer using OpenAI models.
Implements legal, risk, valuation, and synthesis analysis modules.
"""
import logging
import json
import os
from typing import Dict, Optional
from openai import OpenAI, APIError, Timeout

logger = logging.getLogger(__name__)


class AnalysisIntelligence:
    """
    Provides AI analysis methods for due diligence.
    Uses OpenAI GPT models to analyze real estate documents.
    """

    def __init__(self, api_key: str, model: str = "gpt-4", timeout: int = 120):
        """
        Initialize OpenAI client.

        Args:
            api_key: OpenAI API key
            model: Model to use (gpt-4, gpt-3.5-turbo, etc)
            timeout: API call timeout in seconds
        """
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key)

        logger.info(f"OpenAI client initialized with model: {model}")

    def analyze_legal_risks(self, document_text: str, regulation_context: str = "") -> Dict:
        """
        Analyze legal risks in a real estate document.

        Args:
            document_text: Extracted text from document
            regulation_context: Tunisian regulations relevant to analysis

        Returns:
            Dictionary with legal analysis findings
        """
        try:
            logger.info("Starting legal risk analysis...")

            prompt = f"""
You are a real estate lawyer specializing in Tunisian law. Analyze the following property document for legal risks.

DOCUMENT:
{document_text}

RELEVANT REGULATIONS:
{regulation_context if regulation_context else "Standard Tunisian real estate law"}

Please provide analysis in JSON format with:
- identified_risks: List of legal risks found
- compliance_issues: Any regulatory non-compliance
- recommendations: Suggested actions
- risk_level: "high", "medium", or "low"
- confidence: Score 0-100

Return ONLY valid JSON, no markdown.
"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a real estate legal analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature = more focused/consistent
                timeout=self.timeout
            )

            result_text = response.choices[0].message.content
            result = json.loads(result_text)

            logger.info(f"Legal analysis completed: {result.get('risk_level')} risk detected")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse legal analysis JSON: {str(e)}")
            return {
                "error": "Failed to parse analysis result",
                "raw_response": result_text
            }
        except APIError as e:
            logger.error(f"OpenAI API error during legal analysis: {str(e)}")
            return {"error": f"API error: {str(e)}"}
        except Timeout:
            logger.error(f"Legal analysis timed out after {self.timeout}s")
            return {"error": "Analysis timeout"}
        except Exception as e:
            logger.error(f"Unexpected error in legal analysis: {str(e)}")
            return {"error": f"Unexpected error: {str(e)}"}

    def analyze_financial_risk(self, document_text: str, regulation_context: str = "") -> Dict:
        """
        Analyze financial and investment risks.

        Args:
            document_text: Extracted text from document
            regulation_context: Market regulations and standards

        Returns:
            Dictionary with financial risk analysis
        """
        try:
            logger.info("Starting financial risk analysis...")

            prompt = f"""
You are a real estate investment analyst specializing in Tunisian properties. Analyze the following document for financial risks.

DOCUMENT:
{document_text}

MARKET CONTEXT:
{regulation_context if regulation_context else "Standard Tunisian real estate market"}

Please provide analysis in JSON format with:
- investment_risks: Key financial risks
- market_assessment: Market attractiveness assessment
- estimated_roi_range: Expected return on investment range
- risk_factors: Main risk factors
- recommendations: Investment suggestions
- risk_score: 0-100 (100 = highest risk)

Return ONLY valid JSON, no markdown.
"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a financial analyst for real estate."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                timeout=self.timeout
            )

            result_text = response.choices[0].message.content
            result = json.loads(result_text)

            logger.info(f"Financial analysis completed: Risk score {result.get('risk_score')}")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse financial analysis JSON: {str(e)}")
            return {"error": "Failed to parse analysis result"}
        except Exception as e:
            logger.error(f"Error in financial analysis: {str(e)}")
            return {"error": f"Analysis error: {str(e)}"}

    def analyze_valuation(self, document_text: str, regulation_context: str = "") -> Dict:
        """
        Analyze property valuation metrics.

        Args:
            document_text: Extracted text from document
            regulation_context: Market data and standards

        Returns:
            Dictionary with valuation analysis
        """
        try:
            logger.info("Starting valuation analysis...")

            prompt = f"""
You are a commercial property valuation expert for Tunisian real estate. Analyze the following property document.

DOCUMENT:
{document_text}

MARKET DATA:
{regulation_context if regulation_context else "Current Tunisian property market data"}

Please provide analysis in JSON format with:
- property_characteristics: Key features identified
- valuation_method: Method used (comparative, income, cost)
- estimated_value_range: Min and max estimated value
- comparable_properties: Similar properties mentioned
- valuation_confidence: "high", "medium", or "low"
- factors_affecting_value: What factors influence price

Return ONLY valid JSON, no markdown.
"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a real estate valuation expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                timeout=self.timeout
            )

            result_text = response.choices[0].message.content
            result = json.loads(result_text)

            logger.info("Valuation analysis completed")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse valuation JSON: {str(e)}")
            return {"error": "Failed to parse valuation result"}
        except Exception as e:
            logger.error(f"Error in valuation analysis: {str(e)}")
            return {"error": f"Analysis error: {str(e)}"}

    def synthesize_analysis(
        self,
        legal_result: Dict,
        risk_result: Dict,
        valuation_result: Dict,
        document_summary: str
    ) -> Dict:
        """
        Create final synthesis combining all analysis modules.

        Args:
            legal_result: Output from legal analysis
            risk_result: Output from financial risk analysis
            valuation_result: Output from valuation analysis
            document_summary: Brief summary of document

        Returns:
            Final investment decision and recommendations
        """
        try:
            logger.info("Starting synthesis analysis...")

            prompt = f"""
You are an investment decision maker reviewing a real estate opportunity in Tunisia.
Review the following analysis reports and make a final recommendation.

LEGAL ANALYSIS:
{json.dumps(legal_result, indent=2)}

FINANCIAL RISK ANALYSIS:
{json.dumps(risk_result, indent=2)}

VALUATION ANALYSIS:
{json.dumps(valuation_result, indent=2)}

DOCUMENT SUMMARY:
{document_summary}

Please provide final decision in JSON format with:
- overall_recommendation: "GO", "CONDITIONAL", or "NO_GO"
- investment_score: 0-100 (100 = excellent opportunity)
- key_strengths: Top 3 positive factors
- key_concerns: Top 3 concerns or risks
- conditions_for_investment: Conditions that must be met (if CONDITIONAL)
- next_steps: Recommended due diligence steps
- confidence: "high", "medium", or "low"

Return ONLY valid JSON, no markdown.
"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert real estate investment decision maker."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                timeout=self.timeout
            )

            result_text = response.choices[0].message.content
            result = json.loads(result_text)

            logger.info(f"Synthesis completed: Recommendation = {result.get('overall_recommendation')}")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse synthesis JSON: {str(e)}")
            return {"error": "Failed to parse synthesis result"}
        except Exception as e:
            logger.error(f"Error in synthesis: {str(e)}")
            return {"error": f"Analysis error: {str(e)}"}


# Global instance
def get_analysis_intelligence():
    """Get or create analysis intelligence instance."""
    from config import settings

    if not settings.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not set")
        return None

    return AnalysisIntelligence(
        api_key=settings.OPENAI_API_KEY,
        model=settings.OPENAI_MODEL,
        timeout=settings.OPENAI_TIMEOUT_SECONDS
    )
```

**Key Concepts**:

- **Prompt Engineering**: How you ask the AI determines the quality of response
- **Temperature**: 0.2 = focused/consistent; 0.7 = creative/varied
- **JSON Parsing**: Convert AI response to structured data
- **Error Handling**: API calls can fail; we handle gracefully

### Component 4: Regulation Retrieval (services/regulation_retrieval.py)

Create `services/regulation_retrieval.py`:

```python
"""
Regulation corpus retrieval service.
Provides relevant Tunisian real estate regulations for analysis context.
"""
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class RegulationRetrieval:
    """
    Manages retrieval of relevant regulations for analysis context.
    In production, this would search a dedicated FAISS corpus of regulations.
    """

    def __init__(self, regulations_dir: str = "./regulation_indices"):
        """Initialize regulation retrieval service."""
        self.regulations_dir = Path(regulations_dir)
        self.regulations_dir.mkdir(parents=True, exist_ok=True)

        # In production, would load FAISS index here
        logger.info(f"Regulation retrieval initialized at {self.regulations_dir}")

    def get_relevant_regulations(
        self,
        document_text: str,
        context: str = "general",
        limit: int = 5
    ) -> str:
        """
        Get relevant regulations for a document.

        Args:
            document_text: Document to find regulations for
            context: Type of regulations (general, property_rights, taxes, etc)
            limit: Maximum regulations to return

        Returns:
            Concatenated regulation text for use in prompts
        """
        try:
            # In production, would:
            # 1. Embed document_text
            # 2. Search FAISS index
            # 3. Return top-k regulations

            # For now, return default Tunisian regulations
            default_regulations = self._get_default_regulations(context)

            logger.info(f"Retrieved {len(default_regulations)} regulations for context: {context}")
            return default_regulations

        except Exception as e:
            logger.error(f"Error retrieving regulations: {str(e)}")
            return self._get_default_regulations(context)

    @staticmethod
    def _get_default_regulations(context: str = "general") -> str:
        """Get default Tunisian real estate regulations."""
        regulations = {
            "general": """
Tunisian Real Estate Regulations (Summary):
- Law No. 2007-52 of 2007 on property rights
- Law No. 2005-5 on real estate transactions
- Decree 2006-2322 on property registration
- The property must be registered with the local authority
- All transactions must follow the Civil Code provisions
""",
            "property_rights": """
Property Rights in Tunisia:
- Registration is mandatory for property transfer
- Ownership includes use and enjoyment rights
- Restrictions on foreign ownership in certain areas
- Easements and servitudes must be registered
- Tenancy laws require written lease agreements
""",
            "taxes": """
Tunisian Real Estate Taxation:
- Transfer tax (droits d'enregistrement): approximately 3% of value
- Annual property tax (taxe foncière)
- Capital gains tax on property sales
- Rental income is subject to income tax
- Tax exemptions for primary residence in certain cases
""",
        }

        return regulations.get(context, regulations["general"])
```

**Concept**: In production, this would search a database of regulations using FAISS. For now, it returns default regulations.

### Component 5: Async Task Pipeline (services/analysis_tasks.py)

This is where Celery tasks run.

Create `services/analysis_tasks.py`:

```python
"""
Celery async task definitions for analysis pipeline.
Tasks run in background workers, not in FastAPI process.
"""
import logging
import json
from datetime import datetime

from celery_app import celery_app
from services.database import db_service
from services.analysis_intelligence import get_analysis_intelligence
from services.regulation_retrieval import RegulationRetrieval

logger = logging.getLogger(__name__)


regulation_retrieval = RegulationRetrieval()


@celery_app.task(bind=True, max_retries=3)
def run_analysis_task(self, document_id: int, analysis_id: int):
    """
    Main analysis task that runs in Celery worker.
    Orchestrates all analysis modules and stores results.

    Args:
        self: Celery task context
        document_id: ID of document to analyze
        analysis_id: ID of analysis job
    """
    try:
        logger.info(f"Starting analysis task: document_id={document_id}, analysis_id={analysis_id}")

        # Update status to processing
        db_service.update_analysis_status(analysis_id, "processing", started_at=datetime.utcnow())

        # Get document text
        document = db_service.get_document(document_id)
        extracted = db_service.get_document_text(document_id)

        if not extracted or not extracted.raw_text:
            error_msg = "No extracted text found for document"
            logger.error(error_msg)
            db_service.update_analysis_status(analysis_id, "failed", error=error_msg)
            return

        document_text = extracted.raw_text[:5000]  # Use first 5000 chars for context
        document_summary = f"{document.filename} - {len(document_text)} characters"

        # Log event
        db_service.log_analysis_event(analysis_id, "start", {"text_length": len(document_text)})

        # Get analysis intelligence
        intelligence = get_analysis_intelligence()
        if not intelligence:
            error_msg = "OpenAI not configured"
            logger.error(error_msg)
            db_service.update_analysis_status(analysis_id, "failed", error=error_msg)
            return

        # Get relevant regulations
        regulations = regulation_retrieval.get_relevant_regulations(document_text)

        # ========================================================================
        # Run 3 analysis modules in sequence (can be parallelized with Celery)
        # ========================================================================

        # 1. Legal analysis
        logger.info(f"Running legal analysis...")
        legal_result = intelligence.analyze_legal_risks(document_text, regulations)
        db_service.log_analysis_event(analysis_id, "legal_complete", legal_result)

        # 2. Financial risk analysis
        logger.info(f"Running financial risk analysis...")
        risk_result = intelligence.analyze_financial_risk(document_text, regulations)
        db_service.log_analysis_event(analysis_id, "risk_complete", risk_result)

        # 3. Valuation analysis
        logger.info(f"Running valuation analysis...")
        valuation_result = intelligence.analyze_valuation(document_text, regulations)
        db_service.log_analysis_event(analysis_id, "valuation_complete", valuation_result)

        # 4. Synthesis
        logger.info(f"Running synthesis analysis...")
        final_result = intelligence.synthesize_analysis(
            legal_result,
            risk_result,
            valuation_result,
            document_summary
        )
        db_service.log_analysis_event(analysis_id, "synthesis_complete", final_result)

        # Save all outputs to database
        db_service.save_analysis_outputs(
            analysis_id,
            legal_json=json.dumps(legal_result),
            risk_json=json.dumps(risk_result),
            valuation_json=json.dumps(valuation_result),
            final_json=json.dumps(final_result)
        )

        # Mark as complete
        db_service.update_analysis_status(
            analysis_id,
            "done",
            finished_at=datetime.utcnow()
        )

        logger.info(f"Analysis task completed successfully: analysis_id={analysis_id}")

    except Exception as exc:
        logger.error(f"Error in analysis task: {str(exc)}", exc_info=True)

        # Retry up to 3 times with exponential backoff
        if self.request.retries < self.max_retries:
            retry_delay = 2 ** self.request.retries  # 2s, 4s, 8s
            logger.info(f"Retrying analysis task in {retry_delay}s...")
            raise self.retry(exc=exc, countdown=retry_delay)
        else:
            # Final failure
            db_service.update_analysis_status(
                analysis_id,
                "failed",
                error=f"Analysis failed after {self.max_retries} retries: {str(exc)}",
                finished_at=datetime.utcnow()
            )
```

**Key Concepts**:

- **@celery_app.task**: Decorator that turns a function into a Celery task
- **bind=True**: Task can call itself (for retries)
- **max_retries**: Automatically retry if task fails
- **Sequential execution**: Tasks run one after another (can be parallelized)

### Component 6: Worker Entry Point (worker.py)

Create `worker.py`:

```python
"""
Celery worker process entry point.
Runs in separate process, listening for tasks from Redis queue.

To start the worker:
    celery -A celery_app worker -l info
"""
import logging
from celery_app import celery_app

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting Celery worker...")
    celery_app.worker_main([
        "worker",
        "-l", "info",
        "-c", "4",  # 4 concurrent tasks
    ])
```

**What it does**: Starts a Celery worker that listens for tasks.

### Component 7: Update main.py

Add these imports to the top of `main.py`:

```python
from services.analysis_tasks import run_analysis_task
```

Add these new endpoints before the exception handlers:

```python
@app.post(
    "/analyze",
    response_model=AnalyzeCreateResponse,
    summary="Create analysis job",
    tags=["Analysis"]
)
async def create_analysis(request: AnalyzeRequest):
    """
    Create an asynchronous analysis job.
    Returns immediately with job ID. Poll /analyze/{id} for results.

    Analysis includes:
    - Legal risk assessment
    - Financial risk analysis
    - Property valuation
    - Final investment decision

    Args:
        request: { document_id: int }

    Returns:
        { analysis_id, status: "queued" }
    """
    try:
        # Verify document exists
        document = db_service.get_document(request.document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Create analysis record
        analysis = db_service.create_analysis(request.document_id)

        # Enqueue Celery task
        task = run_analysis_task.delay(request.document_id, analysis.id)
        logger.info(f"Analysis job created: {analysis.id}, task_id: {task.id}")

        return AnalyzeCreateResponse(
            analysis_id=analysis.id,
            document_id=request.document_id,
            status="queued",
            message="Analysis queued. Poll GET /analyze/{analysis_id} for results."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create analysis")


@app.get(
    "/analyze/{analysis_id}",
    response_model=AnalysisStatusResponse,
    summary="Get analysis status and results",
    tags=["Analysis"]
)
async def get_analysis(analysis_id: int):
    """
    Get analysis job status and results if complete.

    Returns during processing: { status: "processing" }
    Returns when complete: { status: "done", outputs: {...} }
    Returns on failure: { status: "failed", error: "..." }
    """
    try:
        analysis = db_service.get_analysis(analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")

        response = {
            "analysis_id": analysis_id,
            "document_id": analysis.document_id,
            "status": analysis.status,
            "started_at": analysis.started_at,
            "finished_at": analysis.finished_at,
            "error": analysis.error
        }

        # If complete, include outputs
        if analysis.status == "done":
            outputs = db_service.get_analysis_outputs(analysis_id)
            if outputs:
                response["outputs"] = {
                    "legal": json.loads(outputs.legal_json) if outputs.legal_json else None,
                    "risk": json.loads(outputs.risk_json) if outputs.risk_json else None,
                    "valuation": json.loads(outputs.valuation_json) if outputs.valuation_json else None,
                    "final": json.loads(outputs.final_json) if outputs.final_json else None,
                }

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get analysis")
```

### Component 8: Update Configuration (config.py)

Add these settings:

```python
# Celery Configuration
CELERY_BROKER_URL: str = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

# OpenAI Configuration
OPENAI_API_KEY: str = ""  # Set from .env
OPENAI_MODEL: str = "gpt-4"
OPENAI_BASE_URL: str = ""  # Leave empty for default; override for Azure/other
OPENAI_TIMEOUT_SECONDS: int = 120
```

### Component 9: Update requirements.txt

Add these packages:

```
celery==5.4.0
redis==5.0.7
openai>=1.61.0
```

### Component 10: Update docker-compose.yml

Add Redis and Worker services:

```yaml
version: "3.8"

services:
  # Existing PostgreSQL service (from Stage 1)
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: document_management
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # New: Redis message queue
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  # New: Celery Worker
  worker:
    build: .
    command: python -m celery -A celery_app worker -l info -c 4
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/document_management
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/1
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      OPENAI_MODEL: ${OPENAI_MODEL:-gpt-4}

  # Existing API service (from Stage 1)
  api:
    build: .
    command: python main.py
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/document_management
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/1
      OPENAI_API_KEY: ${OPENAI_API_KEY}

volumes:
  postgres_data:
  redis_data:
```

---

## Testing the Analysis Pipeline

### Test 1: Setup

```bash
# Create .env file
cat > .env << EOF
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/document_management
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
OPENAI_API_KEY=your_actual_key_here
OPENAI_MODEL=gpt-4
OPENAI_TIMEOUT_SECONDS=120
EOF
```

### Test 2: Start Services Locally

```bash
# Terminal 1: Start PostgreSQL
brew services start postgresql

# Terminal 2: Start Redis
redis-server

# Terminal 3: Install requirements
source venv/bin/activate
pip install -r requirements.txt

# Terminal 4: Start Celery worker
celery -A celery_app worker -l info

# Terminal 5: Start FastAPI
python main.py
```

### Test 3: Test Analysis Pipeline

```bash
# 1. Upload a document (from Stage 1)
curl -X POST "http://localhost:8000/upload" \
  -F "file=@sample.pdf" \
  -F "document_type=property_listing"
# Returns: { "success": true, "document_id": 1 }

# 2. Start analysis (returns immediately)
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"document_id": 1}'
# Returns: { "analysis_id": 1, "status": "queued" }

# 3. Poll for results
curl "http://localhost:8000/analyze/1"
# First: { "status": "processing" }
# Later: { "status": "done", "outputs": {...} }
```

---

## Running with Docker

### Simplest Approach

```bash
# Set environment variables
export OPENAI_API_KEY="your_key_here"
export OPENAI_MODEL="gpt-4"

# Start everything
docker compose up --build
```

Docker automatically:

- ✅ Starts PostgreSQL
- ✅ Starts Redis
- ✅ Starts Celery worker
- ✅ Starts FastAPI
- ✅ Creates databases
- ✅ Installs all dependencies

### View Logs

```bash
# All services
docker compose logs -f

# Just the worker
docker compose logs -f worker

# Just the API
docker compose logs -f api
```

### Stop Everything

```bash
docker compose down
```

---

## Glossary of Technical Terms

| Term                    | Simple Explanation                          | Used In                       |
| ----------------------- | ------------------------------------------- | ----------------------------- |
| **Async/Asynchronous**  | Not waiting for result right away           | Task queue model              |
| **Synchronous**         | Waiting for result before moving on         | Traditional API calls         |
| **Queue**               | Line of items waiting to be processed       | Redis stores tasks            |
| **Task**                | A unit of work to be done                   | Analysis job                  |
| **Broker**              | System that distributes tasks to workers    | Redis holds tasks             |
| **Worker**              | Process that does the work                  | Celery worker processes tasks |
| **Celery**              | Python library for async tasks              | Running background jobs       |
| **Redis**               | Fast in-memory database                     | Stores task queue             |
| **Enqueue**             | Add task to queue                           | `run_analysis_task.delay()`   |
| **Polling**             | Repeatedly asking "is it done yet?"         | Calling GET /analyze/{id}     |
| **Webhook**             | Callback when task completes                | Alternative to polling        |
| **OpenAI API**          | Service to call GPT models                  | AI analysis                   |
| **Prompt**              | Text instruction to AI model                | What we ask the AI            |
| **Temperature**         | AI creativity level (0=focused, 1=creative) | API parameter                 |
| **Serialization**       | Converting data to storable format          | JSON for Redis                |
| **Deserialization**     | Converting back from storage                | JSON from Redis               |
| **Idempotent**          | Same result regardless of retries           | Task can safely retry         |
| **Exponential Backoff** | Wait longer for each retry (2s, 4s, 8s)     | Retry strategy                |
| **Context Window**      | Amount of text AI can process               | GPT-4: 8K-128K tokens         |
| **Token**               | Unit of text (roughly 4 chars)              | API billing and limits        |

---

## Summary

You've extended your system with **asynchronous AI-powered analysis**:

✅ **Asynchronous Task Queue** (Celery + Redis)  
✅ **OpenAI Integration** (4 analysis modules)  
✅ **Background Processing** (Doesn't block API)  
✅ **Status Tracking** (Poll for results)  
✅ **Data Persistence** (Store all analysis outputs)  
✅ **Docker Orchestration** (Full stack deployment)

### Key Improvements Over Stage 1

| Aspect              | Stage 1          | Stage 2               |
| ------------------- | ---------------- | --------------------- |
| **Analysis Speed**  | ❌ Blocks user   | ✅ Runs in background |
| **API Response**    | 5-10 seconds     | <1 second             |
| **User Experience** | ⏳ User waits    | ✅ User sees progress |
| **Scalability**     | Limited to 1 API | ✅ Add more workers   |
| **Intelligence**    | Rule-based       | ✅ AI-powered         |

### Next Steps (Stage 3?)

Possibilities:

- **Report Generation** - Convert analysis to PDF
- **Material Detection** - Extract materials from photos
- **Cost Prediction** - ML-based cost forecasting
- **Frontend UI** - Web dashboard
- **Portfolio Management** - Track multiple properties
- **Notifications** - Email/SMS when analysis completes

---

**Congratulations!** You've built a **production-grade backend** with async processing and OpenAI integration! 🎉
