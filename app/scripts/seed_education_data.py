"""
Seed script to populate initial course data
Run with: python -m app.scripts.seed_education_data
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.database import SessionLocal
from app.crud.education import create_course, get_courses
from app.schemas.education import (
    CourseCreate,
    LessonBase,
    LessonType,
    CourseLevel,
)


def seed_education_data():
    """Seed initial course data"""
    db = SessionLocal()

    try:
        # Check if courses already exist
        existing_courses = get_courses(db, limit=1)
        if existing_courses:
            print("⚠️  Courses already exist in database. Skipping seed to avoid duplicates.")
            print("   To re-seed, first drop the tables or delete existing courses.")
            return
        # Courses data
        courses_data = [
            {
                "course": {
                    "title": "Stock Market Fundamentals",
                    "description": "Learn the basics of stock trading, market analysis, and investment strategies",
                    "level": CourseLevel.BEGINNER,
                    "duration": "3h 20min",
                    "modules": 8,
                    "category": "Stocks",
                    "instructor": "Jane Smith",
                    "icon": "TrendingUp",
                },
                "lessons": [
                    LessonBase(
                        title="Introduction to Stock Market",
                        duration="15 min",
                        type=LessonType.VIDEO,
                        video_url="/videos/lesson.mp4",
                        order=1,
                    ),
                    LessonBase(
                        title="Market Participants & Exchanges",
                        duration="20 min",
                        type=LessonType.DESCRIPTION,
                        content="Market Participants\nMarket participants in the stock market include a diverse range of entities:\n\nIndividual Investors: Private persons who buy and sell stocks for personal investment and wealth growth.\n\nInstitutional Investors: Large entities such as mutual funds, pension funds, hedge funds, and insurance companies that trade large volumes of stocks.\n\nBrokers and Broker-Dealers: Brokers act as intermediaries for investors, executing buy and sell orders on their behalf, while broker-dealers can trade for themselves and others.\n\nMarket Makers and Dealers: Firms that provide liquidity by continuously quoting buy and sell prices, helping to reduce price volatility.\n\nPortfolio Managers: Professionals who manage investment portfolios for institutional or individual clients, making buy and sell decisions.\n\nInvestment Bankers: They facilitate companies going public (IPOs), mergers, and acquisitions, assisting in compliance with regulatory authorities.\n\nCustodians and Depository Participants: Institutions that hold and safeguard securities on behalf of investors and facilitate the transfer of securities.\n\nArbitrageurs and Algorithmic Traders: Those who seek to profit from price inefficiencies and help maintain market efficiency by trading at high speeds.\n\nRegulators and Government Entities: Ensure markets operate fairly and transparently under established laws and regulations.\n\nStock Exchanges\nStock exchanges are organized marketplaces where stocks and other securities are traded between buyers and sellers. Key points about exchanges:\n\nThey provide platforms for companies to raise capital by issuing shares in the primary market (e.g., IPOs).\n\nAfter issuance, shares trade in the secondary market where investors buy and sell among themselves.\n\nExchanges match buy and sell orders electronically or on physical trading floors (e.g., NYSE).\n\nExchanges rely on market makers to maintain liquidity and facilitate smooth price discovery.\n\nExamples of major exchanges include the New York Stock Exchange (NYSE), Nasdaq, and many others worldwide.\n\nExchanges charge transaction fees for facilitating trades.\n\nTogether, these market participants and exchanges create a dynamic ecosystem where capital flows efficiently from investors to companies, supporting economic growth and investment opportunities for the public. This system is regulated to protect investors and ensure transparency and fairness in trading.",
                        order=2,
                    ),
                    LessonBase(
                        title="Stock Analysis Fundamentals",
                        duration="25 min",
                        type=LessonType.VIDEO,
                        video_url="/videos/lesson.mp4",
                        order=3,
                    ),
                    LessonBase(
                        title="Practice: Analyzing AAPL",
                        duration="30 min",
                        type=LessonType.PRACTICE,
                        order=4,
                    ),
                    LessonBase(
                        title="Understanding Stock Prices & Quotes",
                        duration="25 min",
                        type=LessonType.VIDEO,
                        video_url="/videos/lesson.mp4",
                        order=5,
                    ),
                    LessonBase(
                        title="Dividends & Stock Splits",
                        duration="20 min",
                        type=LessonType.VIDEO,
                        video_url="/videos/lesson.mp4",
                        order=6,
                    ),
                    LessonBase(
                        title="Investment Strategies",
                        duration="35 min",
                        type=LessonType.VIDEO,
                        video_url="/videos/lesson.mp4",
                        order=7,
                    ),
                    LessonBase(
                        title="Building Your First Portfolio",
                        duration="30 min",
                        type=LessonType.PRACTICE,
                        order=8,
                    ),
                ],
            },
            {
                "course": {
                    "title": "Options Trading Mastery",
                    "description": "Advanced options strategies, Greeks, and risk management techniques",
                    "level": CourseLevel.ADVANCED,
                    "duration": "5h 15min",
                    "modules": 11,
                    "category": "Options",
                    "instructor": "Mike Johnson",
                    "icon": "Target",
                },
                "lessons": [
                    LessonBase(title="Options Basics", duration="20 min", type=LessonType.VIDEO, video_url="/videos/lesson.mp4", order=1),
                    LessonBase(title="The Greeks Explained", duration="30 min", type=LessonType.VIDEO, video_url="/videos/lesson.mp4", order=2),
                    LessonBase(title="Covered Calls Strategy", duration="25 min", type=LessonType.VIDEO, video_url="/videos/lesson.mp4", order=3),
                    LessonBase(title="Cash-Secured Puts (CSP)", duration="30 min", type=LessonType.VIDEO, video_url="/videos/lesson.mp4", order=4),
                    LessonBase(title="Straddles & Strangles", duration="30 min", type=LessonType.VIDEO, video_url="/videos/lesson.mp4", order=5),
                    LessonBase(title="Iron Condors & Butterflies", duration="35 min", type=LessonType.VIDEO, video_url="/videos/lesson.mp4", order=6),
                    LessonBase(title="Risk Management in Options", duration="30 min", type=LessonType.VIDEO, video_url="/videos/lesson.mp4", order=7),
                    LessonBase(title="Volatility Trading", duration="25 min", type=LessonType.VIDEO, video_url="/videos/lesson.mp4", order=8),
                    LessonBase(title="Options Assignment & Exercise", duration="20 min", type=LessonType.VIDEO, video_url="/videos/lesson.mp4", order=9),
                    LessonBase(title="Options Portfolio Management", duration="30 min", type=LessonType.VIDEO, video_url="/videos/lesson.mp4", order=10),
                    LessonBase(title="Practice: Building Options Strategies", duration="40 min", type=LessonType.PRACTICE, order=11),
                ],
            },
            {
                "course": {
                    "title": "Cryptocurrency Trading",
                    "description": "Digital assets, DeFi, and crypto market dynamics",
                    "level": CourseLevel.INTERMEDIATE,
                    "duration": "45 min",
                    "modules": 2,
                    "category": "Crypto",
                    "instructor": "Sarah Chen",
                    "icon": "DollarSign",
                },
                "lessons": [
                    LessonBase(title="Crypto Basics & Wallets", duration="25 min", type=LessonType.VIDEO, video_url="/videos/lesson.mp4", order=1),
                    LessonBase(title="Trading Platforms", duration="20 min", type=LessonType.VIDEO, video_url="/videos/lesson.mp4", order=2),
                ],
            },
            {
                "course": {
                    "title": "Futures Trading Essentials",
                    "description": "Master futures contracts, hedging, and market speculation strategies",
                    "level": CourseLevel.ADVANCED,
                    "duration": "1h 30min",
                    "modules": 3,
                    "category": "Futures",
                    "instructor": "Robert Anderson",
                    "icon": "TrendingUp",
                },
                "lessons": [
                    LessonBase(title="Understanding Futures Contracts", duration="25 min", type=LessonType.VIDEO, video_url="/videos/lesson.mp4", order=1),
                    LessonBase(title="Futures vs Options", duration="30 min", type=LessonType.VIDEO, video_url="/videos/lesson.mp4", order=2),
                    LessonBase(title="Hedging Strategies", duration="35 min", type=LessonType.VIDEO, video_url="/videos/lesson.mp4", order=3),
                ],
            },
            {
                "course": {
                    "title": "Forex & Commodities",
                    "description": "Currency pairs, commodity markets, and global economics",
                    "level": CourseLevel.ADVANCED,
                    "duration": "45 min",
                    "modules": 2,
                    "category": "Forex",
                    "instructor": "Emma Wilson",
                    "icon": "Zap",
                },
                "lessons": [
                    LessonBase(title="Forex Market Basics", duration="20 min", type=LessonType.VIDEO, video_url="/videos/lesson.mp4", order=1),
                    LessonBase(title="Currency Pairs Explained", duration="25 min", type=LessonType.VIDEO, video_url="/videos/lesson.mp4", order=2),
                ],
            },
        ]

        # Create courses
        for course_data in courses_data:
            course_create = CourseCreate(**course_data["course"], lessons=course_data["lessons"])
            create_course(db, course_create)
            print(f"✓ Created course: {course_data['course']['title']}")

        print("\n✅ Course data seeded successfully!")

    except Exception as e:
        print(f"\n❌ Error seeding data: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_education_data()
