CREATE TABLE stock_data.stock_staging_table(
					id SERIAL PRIMARY KEY,
					DATE TEXT,
					Close_AAPL TEXT, 
					Close_NVDA TEXT, 
					High_AAPL TEXT, 
					High_NVDA TEXT, 
					Low_AAPL TEXT,
       				Low_NVDA TEXT, 
					Open_AAPL TEXT, 
					Open_NVDA TEXT, 
					Volume_AAPL TEXT, 
					Volume_NVDA TEXT
);



CREATE TABLE stock_data.stock_live_table (
    id                     VARCHAR(36)   NOT NULL,
    stock_valuation_date   DATE     NOT NULL,
    stock                  VARCHAR(10)   NOT NULL,
    close_value            NUMERIC(12,4) NOT NULL,
    high_value             NUMERIC(12,4) NOT NULL,
    low_value              NUMERIC(12,4) NOT NULL,
    open_value             NUMERIC(12,4) NOT NULL,
    volume_value           NUMERIC(18,0) NOT NULL
)
DISTKEY (stock)
SORTKEY (stock_valuation_date);


CREATE TABLE stock_data.highest_lowest_stock_metric(
					id VARCHAR(36)   NOT NULL,
					stock VARCHAR(10)   NOT NULL,
					highest_lowest_valuation_key INTEGER NOT NULL, 
					start_date DATE     NOT NULL,
					end_date DATE     NOT NULL,
                    day_length INTERVAL NOT NULL
)
DISTKEY (stock)
SORTKEY (stock_valuation_date);

CREATE TABLE stock_data.moving_average_stock_metric(
					id VARCHAR(36)   NOT NULL,
					stock VARCHAR(10)   NOT NULL,
					moving_average_valuation_key INTEGER NOT NULL, 
					start_date DATE     NOT NULL,
					end_date DATE     NOT NULL,
                    day_length INTERVAL NOT NULL
			)
DISTKEY (stock)
SORTKEY (stock_valuation_date);


CREATE TABLE stock_data.stock_average_metric(
					id VARCHAR(36)   NOT NULL,
					stock VARCHAR(10)   NOT NULL,
					stock_average_valuation_key INTEGER NOT NULL, 
					start_date DATE NOT NULL,
					end_date DATE NOT NULL,
                    day_length INTERVAL NOT NULL
)
DISTKEY (stock)
SORTKEY (stock_valuation_date);




--central snapshot table
CREATE TABLE stock_data.stock_last_snapshot_table(
                id UUID VARCHAR(36)   NOT NULL,
                stock_valuation_date DATE NOT NULL,
                stock VARCHAR(10)   NOT NULL,
                close_value NUMERIC(12,4) NOT NULL,
                highest_lowest_valuation ath_atl NOT NULL,
                minimum_close NUMERIC(12,4) NOT NULL,
                maximum_close NUMERIC(12,4) NOT NULL,
                average_valuation rolling_average NOT NULL,
                moving_avg_comparison moving_average_crossover NOT NULL
);




--dim tables
CREATE TABLE stock_data.highest_lowest_valuation_dim(
                id SERIAL PRIMARY KEY,
                bucket_name ath_atl NOT NULL,
                bucket_description TEXT NOT NULL
)

INSERT INTO stock_data.highest_lowest_valuation_dim (id,bucket_name,bucket_description)
VALUES (1,'near_record_low','when the division between close value and minimum close value is equal or lower than 20% of the maximum and minimum close value difference '),
		 (2,'lower_range','when the division between close value and minimum close value is equal or lower than 40% of the maximum and minimum close value difference '),
		 (3,'mid_range','when the division between close value and minimum close value is equal or lower than 60% of the maximum and minimum close value difference '),
		 (4,'higher_range','when the division between close value and minimum close value is equal or lower than 80% the maximum and minimum close value difference '),
		 (5,'near_record_high','when the division between close value and minimum close value is greater than 80% of the maximum and minimum close value difference ')


CREATE TABLE stock_data.average_valuation_dim(
                id SERIAL PRIMARY KEY,
                bucket_name rolling_average NOT NULL,
                bucket_description TEXT NOT NULL
)

INSERT INTO stock_data.average_valuation_dim (id,bucket_name,bucket_description)
VALUES (1,'above','when close value is lower than the difference between average close value and standard deviation'),
		 (2,'below','when close value is above than the addition of average close value and standard deviation'),
		 (3,'within','when close value is between above and below')




CREATE TABLE stock_data.moving_avg_comparison_dim(
                id SERIAL PRIMARY KEY,
                bucket_name moving_average_crossover NOT NULL,
                bucket_description TEXT NOT NULL
)

INSERT INTO stock_data.moving_avg_comparison_dim (id,bucket_name,bucket_description)
VALUES (1,'bullish_alignment','when avg of last 50 days is greater than avg of last 200 days'),
		 (2,'bearish_alignment','when avg of last 50 days is lower than avg of last 200 days')




















--types
CREATE TYPE ath_atl AS ENUM (
    'near_record_low',
    'lower_range',
    'mid_range',
    'higher_range',
    'near_record_high'
);

CREATE TYPE high_low_streak_main(
    stock TEXT,
    highest_lowest_valuation ath_atl,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    day_length INTERVAL
)



CREATE TYPE moving_average_crossover AS ENUM (
    'bullish_alignment',
    'bearish_alignment'
);

CREATE TYPE moving_avg_array(
    stock TEXT,
    moving_avg_comparison moving_average_crossover,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    day_length INTERVAL
)



CREATE TYPE rolling_average AS ENUM (
    'above',
    'below',
	'within'
);


CREATE TYPE stock_streak_row AS(
	id UUID,
    stock TEXT,
    average_valuation INTEGER,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    day_length INTERVAL
);

CREATE TYPE moving_avg_array AS(
	id UUID,
    stock TEXT,
    moving_avg_comparison INTEGER,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    day_length INTERVAL
);


CREATE TYPE stock_data.moving_avg_array AS(
	id UUID,
    stock TEXT,
    moving_avg_comparison INTEGER,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    day_length INTERVAL
);