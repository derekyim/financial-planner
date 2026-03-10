"""
Integration tests for SlidesUtilities class.

Tests that the Google Slides API is accessible and that we can add slides
to the presentation configured in GOOGLE_SLIDES_URL.

Requires:
    - Valid service account credentials file
    - Google Slides API enabled in the GCP project
    - The presentation shared with the service account email (Editor)

Run with: pytest integration_tests/test_slides_utilities.py -v -s
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

root_env = os.path.join(os.path.dirname(__file__), "../../.env")
load_dotenv(dotenv_path=root_env)

from shared.slides_utilities import SlidesUtilities
from googleapiclient.errors import HttpError

pytestmark = pytest.mark.integration

CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "../credentials.json")
SLIDES_URL = os.getenv("GOOGLE_SLIDES_URL", "")
SERVICE_ACCOUNT_EMAIL = "dy-gsheets-access-2@dy-ai-477300.iam.gserviceaccount.com"


@pytest.fixture(scope="module")
def slides_client() -> SlidesUtilities:
    if not os.path.exists(CREDENTIALS_PATH):
        pytest.skip(f"Credentials file not found at {CREDENTIALS_PATH}")
    if not SLIDES_URL:
        pytest.skip("GOOGLE_SLIDES_URL not set in environment")
    print(f"\nCredentials: {CREDENTIALS_PATH}")
    print(f"Slides URL: {SLIDES_URL}")
    return SlidesUtilities(CREDENTIALS_PATH)


@pytest.fixture(scope="module")
def presentation_id() -> str:
    if not SLIDES_URL:
        pytest.skip("GOOGLE_SLIDES_URL not set")
    pres_id = SlidesUtilities.extract_presentation_id(SLIDES_URL)
    print(f"Presentation ID: {pres_id}")
    return pres_id


def _check_permission(func, *args, **kwargs):
    """Run a Slides API call and give a clear message on 403."""
    try:
        return func(*args, **kwargs)
    except HttpError as e:
        if e.resp.status == 403:
            pytest.fail(
                f"403 Permission Denied — the presentation is not shared "
                f"with the service account.\n\n"
                f"FIX: Open the presentation in Google Slides, click Share, "
                f"and add this email as Editor:\n"
                f"  {SERVICE_ACCOUNT_EMAIL}\n\n"
                f"Raw error: {e}"
            )
        raise


class TestSlidesAccess:
    """Test basic Google Slides API access."""

    def test_extract_presentation_id(self):
        url = "https://docs.google.com/presentation/d/1_f-hT5TQaeJES8z7tKG7DR3dUIz_3BQHVxlRYTdsZuw"
        pres_id = SlidesUtilities.extract_presentation_id(url)
        assert pres_id == "1_f-hT5TQaeJES8z7tKG7DR3dUIz_3BQHVxlRYTdsZuw"

    def test_get_slide_count(self, slides_client, presentation_id):
        count = _check_permission(slides_client.get_slide_count, presentation_id)
        print(f"Current slide count: {count}")
        assert isinstance(count, int)
        assert count >= 0

    def test_add_title_slide(self, slides_client, presentation_id):
        before = _check_permission(slides_client.get_slide_count, presentation_id)
        slide_id = slides_client.add_title_slide(
            presentation_id,
            title="Integration Test — Title Slide",
            subtitle="Created by automated test",
        )
        after = slides_client.get_slide_count(presentation_id)
        print(f"Added title slide: {slide_id} (slides: {before} → {after})")
        assert slide_id.startswith("slide_")
        assert after == before + 1

    def test_add_content_slide(self, slides_client, presentation_id):
        before = _check_permission(slides_client.get_slide_count, presentation_id)
        slide_id = slides_client.add_content_slide(
            presentation_id,
            title="Integration Test — Content Slide",
            body="EBITDA forecast shows a loss of -$1,228,666 for 2026.\n\n"
                 "Cash turns negative in March 2026 and stays negative for "
                 "22 months before recovering in January 2028.",
        )
        after = slides_client.get_slide_count(presentation_id)
        print(f"Added content slide: {slide_id} (slides: {before} → {after})")
        assert slide_id.startswith("slide_")
        assert after == before + 1

    def test_add_bullet_slide(self, slides_client, presentation_id):
        before = _check_permission(slides_client.get_slide_count, presentation_id)
        slide_id = slides_client.add_bullet_slide(
            presentation_id,
            title="Integration Test — Bullet Slide",
            bullets=[
                "Decrease CaC by 18% ($55 → $45)",
                "Increase Ad Spend by 16% ($1.55M → $1.80M)",
                "Increase AoV by 13% ($97 → $110)",
                "Expected result: EBITDA +144%",
            ],
        )
        after = slides_client.get_slide_count(presentation_id)
        print(f"Added bullet slide: {slide_id} (slides: {before} → {after})")
        assert slide_id.startswith("slide_")
        assert after == before + 1


class TestCreatePresentation:
    """Test creating / preparing a presentation via create_presentation().

    This exercises the fallback path: if the SA has no Drive storage,
    create_presentation() will reset GOOGLE_SLIDES_URL (clear slides, rename).
    """

    def test_create_presentation_with_slides(self, slides_client):
        from datetime import date

        today = date.today().strftime("%B %d, %Y")
        title = f"EBITDA Forecast Analysis — {today}"

        pres_id, url = slides_client.create_presentation(title)
        print(f"\nPrepared presentation: {url}")

        assert pres_id
        assert "docs.google.com/presentation/d/" in url

        count = slides_client.get_slide_count(pres_id)
        print(f"Slide count after reset: {count}")
        assert count >= 1

        slides_client.add_title_slide(
            pres_id, title, "Strategic Lever Analysis"
        )
        slides_client.add_bullet_slide(
            pres_id,
            "Key Levers",
            [
                "Customer Acquisition Cost (CaC): $55 → target $45",
                "Direct Advertising: $1.55M → target $1.80M",
                "Average Order Value (AoV): $97 → target $110",
            ],
        )
        slides_client.add_content_slide(
            pres_id,
            "Recommendation",
            "A balanced approach combining an 18% CaC reduction with "
            "16% higher ad spend and 13% AoV growth delivers the "
            "highest probability of reaching $1M EBITDA by Dec 2027.",
        )

        final_count = slides_client.get_slide_count(pres_id)
        print(f"Final slide count: {final_count}")
        print(f"Presentation URL: {url}")
        assert final_count >= 4
