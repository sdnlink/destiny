import unittest
from fastapi.testclient import TestClient

from app.core.db import db_repository
from app.calendar.engine import CalendarEngine, CalendarInput
from app.main import app


class CalendarCorpusAndDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_database_twenty_eight_mansions(self):
        rows = db_repository.get_twenty_eight_mansions()
        self.assertIsNotNone(rows, "twenty_eight_mansions table should be queryable")
        self.assertEqual(len(rows), 28, "There must be exactly 28 mansions")

        # Check quadrants distribution
        quadrants = [r["quadrant"] for r in rows]
        self.assertEqual(quadrants.count("东方苍龙"), 7)
        self.assertEqual(quadrants.count("北方玄武"), 7)
        self.assertEqual(quadrants.count("西方白虎"), 7)
        self.assertEqual(quadrants.count("南方朱雀"), 7)

        # Check first and key mansions
        jiao = rows[0]
        self.assertEqual(jiao["name"], "角")
        self.assertEqual(jiao["beast_spirit"], "角木蛟")
        self.assertEqual(jiao["quadrant"], "东方苍龙")
        self.assertEqual(jiao["ancient_degrees"], 12.0)
        self.assertTrue(len(jiao["song_lyrics"]) > 0)
        self.assertIn("天门", jiao["imagery_meanings"])

        # Filter by quadrant
        dragon_rows = db_repository.get_twenty_eight_mansions(quadrant="东方苍龙")
        self.assertEqual(len(dragon_rows), 7)
        self.assertEqual([r["name"] for r in dragon_rows], ["角", "亢", "氐", "房", "心", "尾", "箕"])

    def test_database_three_enclosures(self):
        rows = db_repository.get_three_enclosures()
        self.assertIsNotNone(rows, "three_enclosures table should be queryable")
        self.assertEqual(len(rows), 3, "There must be exactly 3 enclosures")

        names = [r["name"] for r in rows]
        self.assertEqual(names, ["紫微垣", "太微垣", "天市垣"])

        ziwei = rows[0]
        self.assertEqual(ziwei["name"], "紫微垣")
        self.assertIn("北斗七星", ziwei["key_officials"])
        self.assertIn("勾陈", ziwei["key_officials"])
        self.assertEqual(ziwei["official_count"], 39)

    def test_database_historical_calendars(self):
        rows = db_repository.get_historical_calendars()
        self.assertIsNotNone(rows, "historical_calendars table should be queryable")
        self.assertEqual(len(rows), 10, "There should be 10 major historical calendars")

        cal_map = {r["calendar_id"]: r for r in rows}
        self.assertIn("taichu-calendar", cal_map)
        self.assertIn("daming-calendar", cal_map)
        self.assertIn("shoushi-calendar", cal_map)
        self.assertIn("shixian-calendar", cal_map)

        # Verify Shoushi calendar constants
        shoushi = cal_map["shoushi-calendar"]
        self.assertEqual(shoushi["name"], "授时历")
        self.assertEqual(shoushi["dynasty"], "元代")
        self.assertEqual(shoushi["tropical_year_days"], 365.2425)
        self.assertIn("郭守敬", shoushi["author"])

        # Filter by dynasty
        han_cals = db_repository.get_historical_calendars(dynasty="西汉")
        self.assertEqual(len(han_cals), 1)
        self.assertEqual(han_cals[0]["name"], "太初历")

    def test_database_hetu_numerology(self):
        rows = db_repository.get_hetu_numerology()
        self.assertIsNotNone(rows, "hetu_numerology table should be queryable")
        self.assertEqual(len(rows), 5, "There should be 5 pairs in Hetu")

        # Pair 1: 1-6 Water North
        pair1 = rows[0]
        self.assertEqual(pair1["generating_number"], 1)
        self.assertEqual(pair1["forming_number"], 6)
        self.assertEqual(pair1["element"], "水")
        self.assertEqual(pair1["direction"], "北")
        self.assertEqual(pair1["trigram_later"], "坎")

        # Filter by element
        fire_rows = db_repository.get_hetu_numerology(element="火")
        self.assertEqual(len(fire_rows), 1)
        self.assertEqual(fire_rows[0]["generating_number"], 2)
        self.assertEqual(fire_rows[0]["forming_number"], 7)
        self.assertEqual(fire_rows[0]["direction"], "南")

    def test_database_lunar_phase_regimes(self):
        rows = db_repository.get_lunar_phase_regimes()
        self.assertIsNotNone(rows, "lunar_phase_regimes table should be queryable")
        self.assertEqual(len(rows), 4, "There must be 4 bronze inscription lunar phases")

        codes = [r["phase_code"] for r in rows]
        self.assertEqual(codes, ["chuji", "jishengba", "jiwang", "jisiba"])
        names = [r["name"] for r in rows]
        self.assertEqual(names, ["初吉", "既生霸", "既望", "既死霸"])

    def test_api_constants_twenty_eight_mansions(self):
        response = self.client.get("/v1/constants/twenty-eight-mansions")
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(len(data), 28)

        # Test query parameter filter
        res_filter = self.client.get("/v1/constants/twenty-eight-mansions?quadrant=北方玄武")
        self.assertEqual(res_filter.status_code, 200)
        filtered = res_filter.json()["data"]
        self.assertEqual(len(filtered), 7)
        self.assertEqual(filtered[0]["name"], "斗")

    def test_api_constants_three_enclosures(self):
        response = self.client.get("/v1/constants/three-enclosures")
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]["name"], "紫微垣")

    def test_api_constants_historical_calendars(self):
        response = self.client.get("/v1/constants/historical-calendars")
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(len(data), 10)

        res_filter = self.client.get("/v1/constants/historical-calendars?dynasty=唐代")
        self.assertEqual(res_filter.status_code, 200)
        filtered = res_filter.json()["data"]
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["name"], "大衍历")

    def test_api_constants_hetu_numerology(self):
        response = self.client.get("/v1/constants/hetu-numerology")
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(len(data), 5)

        res_filter = self.client.get("/v1/constants/hetu-numerology?element=木")
        self.assertEqual(res_filter.status_code, 200)
        filtered = res_filter.json()["data"]
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["generating_number"], 3)
        self.assertEqual(filtered[0]["forming_number"], 8)

    def test_api_constants_lunar_phases(self):
        response = self.client.get("/v1/constants/lunar-phases")
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(len(data), 4)

    def test_calendar_engine_astronomical_enrichment(self):
        engine = CalendarEngine()
        result = engine.calculate(CalendarInput(
            local_datetime="2026-08-20T21:00:00",
            timezone="Asia/Shanghai",
        ))
        almanac = result["almanac"]
        self.assertIn("twenty_eight_mansion", almanac)
        mansion = almanac["twenty_eight_mansion"]
        self.assertIn("name", mansion)
        self.assertIn("beast_spirit", mansion)
        self.assertIn("quadrant", mansion)

        self.assertIn("lunar_phase_regime", almanac)
        lunar_phase = almanac["lunar_phase_regime"]
        self.assertIn(lunar_phase["code"], ["chuji", "jishengba", "jiwang", "jisiba"])


if __name__ == "__main__":
    unittest.main()
