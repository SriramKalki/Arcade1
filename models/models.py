from sqlalchemy import create_engine, Column, Integer, Float, String, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class WeatherData(Base):
    __tablename__ = 'weather_data'
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    weather_code = Column(Float)
    temperature_max = Column(Float)
    temperature_min = Column(Float)
    precipitation_sum = Column(Float)
    wind_speed_max = Column(Float)
    precipitation_probability_max = Column(Float)

engine = create_engine('sqlite:///weather_data.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)