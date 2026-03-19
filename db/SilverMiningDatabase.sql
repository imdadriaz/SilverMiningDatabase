-- ===============
-- Create DB
-- ===============
CREATE DATABASE SilverMiningDatabase;
USE SilverMiningDatabase;

-- ===============
-- Create Tables
-- ===============

CREATE TABLE USERTAB(
	User_ID INT AUTO_INCREMENT NOT NULL,
    User_FName VARCHAR(50) NOT NULL,
    User_LName VARCHAR(50) NOT NULL,
    User_Email VARCHAR(100) NOT NULL,
    User_Password VARCHAR(200) NOT NULL,
    Permission_Level ENUM('Investor', 'Admin') NOT NULL,
    CONSTRAINT USERTAB_PK PRIMARY KEY (User_ID)
);

CREATE TABLE COMPANY(
	Ticker VARCHAR(10) NOT NULL,
    Company_Name VARCHAR(50) NOT NULL,
	CONSTRAINT COMPANY_PK PRIMARY KEY (Ticker)
);

CREATE TABLE FAVOURITE(
	Investor_ID INT NOT NULL,
    Ticker VARCHAR(10) NOT NULL,
    DateFavourited DATE NOT NULL,
    CONSTRAINT FAVOURITE_PK PRIMARY KEY (Investor_ID, Ticker),
    CONSTRAINT FAVOURITE_FK_ID
		FOREIGN KEY (Investor_ID)
        REFERENCES USERTAB (User_ID),
	CONSTRAINT FAVOURITE_FK_TICK
		FOREIGN KEY (Ticker)
        REFERENCES COMPANY (Ticker)
);

CREATE TABLE RANKINGREPORT(
	Ticker VARCHAR(10) NOT NULL,
    Score DECIMAL(5,2) NOT NULL,
    RankPosition INT NOT NULL,
    
    CONSTRAINT RANKINGREPORT_PK PRIMARY KEY (Ticker),
    CONSTRAINT RANKINGREPORT_FK
		FOREIGN KEY (Ticker)
        REFERENCES COMPANY (Ticker)
);

CREATE TABLE FINMETRICS(

	Ticker VARCHAR(10) NOT NULL,
    AISC DECIMAL(12,2) NOT NULL,
    PEG	DECIMAL(6,2) NOT NULL,
    TotalDebt DECIMAL(15,2) NOT NULL,
    DebtToEquity DECIMAL(6,2) NOT NULL,
    Revenue DECIMAL(15,2) NOT NULL,
    EBITDA DECIMAL (15,2) NOT NULL,
    LastUpdatedBy INT,
    
    CONSTRAINT FINMETRICS_PK PRIMARY KEY (Ticker),
    CONSTRAINT FINMETRICS_FK_TICK
		FOREIGN KEY (Ticker)
        REFERENCES COMPANY (Ticker),
	CONSTRAINT FINMETRICS_FK_ID
		FOREIGN KEY (LastUpdatedBy)
        REFERENCES USERTAB (User_ID)
);

CREATE TABLE STOCKPRICE (
    Ticker VARCHAR(10) NOT NULL,
    Date_Updated DATE NOT NULL,
    PreviousOpen DECIMAL(10,2),
    PreviousClose DECIMAL(10,2),
    FiftyTwoWeekHigh DECIMAL(10,2),
    FiftyTwoWeekLow DECIMAL(10,2),
    PRIMARY KEY (Ticker, Date_Updated),
    FOREIGN KEY (Ticker) REFERENCES COMPANY(Ticker)
);

CREATE TABLE PRODUCTIONDATA (
    Ticker VARCHAR(10) NOT NULL,
    Period VARCHAR(20) NOT NULL,
    SilverOuncesProduced DECIMAL(15,2),
    Notes TEXT,
    LastUpdatedBy INT,
    CONSTRAINT PRODUCTIONDATA_PK PRIMARY KEY (Ticker, Period),
    CONSTRAINT PRODUCTIONDATA_FK_TICK
		FOREIGN KEY (Ticker) 
		REFERENCES COMPANY(Ticker),
	CONSTRAINT PRODUCTIONDATA_FK_UPDATE
		FOREIGN KEY (LastUpdatedBy) 
		REFERENCES USERTAB(User_ID)
);

CREATE TABLE VIEWSDETAILS (
    InvestorID INT NOT NULL,
    Ticker VARCHAR(10) NOT NULL,
    CONSTRAINT VIEWSDETAILS_PK PRIMARY KEY (InvestorID, Ticker),
    CONSTRAINT VIEWSDETAILS_FK_USER
		FOREIGN KEY (InvestorID) 
        REFERENCES USERTAB(User_ID),
	CONSTRAINT VIEWSDETAILS_FK_TICK
		FOREIGN KEY (Ticker) 
		REFERENCES COMPANY(Ticker)
);

CREATE TABLE UPDATESCOMPANY (
    AdminID INT NOT NULL,
    Ticker VARCHAR(10) NOT NULL,
    CONSTRAINT UPDATESCOMPANY_PK PRIMARY KEY (AdminID, Ticker),
	CONSTRAINT UPDATESCOMPANY_FK_USER
		FOREIGN KEY (AdminID) 
        REFERENCES USERTAB(User_ID),
	CONSTRAINT UPDATESCOMPANY_FK_TICK
		FOREIGN KEY (Ticker) 
		REFERENCES COMPANY(Ticker)
);

CREATE TABLE UPDATESSTOCKPRICE (
    AdminID INT NOT NULL,
    Ticker VARCHAR(10) NOT NULL,
    Date_Updated DATE NOT NULL,
    CONSTRAINT UPDATESSTOCKPRICE_PK PRIMARY KEY (AdminID, Ticker, Date_Updated),
    CONSTRAINT UPDATESSTOCKPRICE_FK_USER
		FOREIGN KEY (AdminID) 
        REFERENCES USERTAB(User_ID),
	CONSTRAINT UPDATESSTOCKPRICE_FK_TICK
		FOREIGN KEY (Ticker) 
        REFERENCES COMPANY(Ticker)
);

CREATE TABLE UPDATESPRODUCTIONDATA (
    AdminID INT NOT NULL,
    Ticker VARCHAR(10) NOT NULL,
    Period VARCHAR(20) NOT NULL,
    CONSTRAINT UPDATESPRODUCTIONDATA_PK PRIMARY KEY (AdminID, Ticker, Period),
    CONSTRAINT UPDATESPRODUCTIONDATA_FK_USER
		FOREIGN KEY (AdminID) 
        REFERENCES USERTAB(User_ID),
    CONSTRAINT UPDATESPRODUCTIONDATA_FK_TICK
    FOREIGN KEY (Ticker) 
    REFERENCES COMPANY(Ticker)
);


-- ===============
-- Insert Data
-- ===============

INSERT INTO USERTAB (User_FName, User_LName, User_Email, User_Password, Permission_Level)
VALUES
('Maad', 'Abbasi', 'maad@email.com', 'pw1', 'Investor'),
('Imdad', 'Goraho', 'slee@email.com', 'pw2', 'Admin'),
('Jade', 'Torres', 'jsmith@emaul.com', 'pw3', 'Investor');

-- User_IDs will be:
-- 1 = Maad (Investor)
-- 2 = Imdad (Admin)
-- 3 = Jade (Investor)



INSERT INTO COMPANY (Ticker, Company_Name)
VALUES
('PAAS', 'Pan American Silver'),
('AG', 'First Majestic Silver'),
('FSM', 'Fortuna Silver Mines');



INSERT INTO FAVOURITE (Investor_ID, Ticker, DateFavourited)
VALUES
(1, 'PAAS', '2024-01-10'),
(1, 'AG', '2024-02-15'),
(3, 'FSM', '2024-03-01');



INSERT INTO RANKINGREPORT (Ticker, Score, RankPosition)
VALUES
('PAAS', 88.50, 1),
('AG', 75.20, 2),
('FSM', 69.80, 3);



INSERT INTO FINMETRICS (Ticker, AISC, PEG, TotalDebt, DebtToEquity, Revenue, EBITDA, LastUpdatedBy)
VALUES
('PAAS', 14.50, 1.20, 500000000, 0.35, 2100000000, 650000000, 2),
('AG', 17.20, 1.80, 300000000, 0.50, 1200000000, 400000000, 2);



INSERT INTO STOCKPRICE (Ticker, Date_Updated, PreviousOpen, PreviousClose, FiftyTwoWeekHigh, FiftyTwoWeekLow)
VALUES
('PAAS', '2024-03-01', 18.50, 19.20, 24.00, 14.00),
('AG', '2024-03-01', 7.80, 8.10, 12.00, 6.00);



INSERT INTO PRODUCTIONDATA (Ticker, Period, SilverOuncesProduced, Notes, LastUpdatedBy)
VALUES
('PAAS', 'Q4-2023', 5200000, 'Strong quarter due to mine expansion.', 2),
('AG', 'Q4-2023', 3100000, 'Lower output due to maintenance.', 2);



INSERT INTO VIEWSDETAILS (InvestorID, Ticker)
VALUES
(1, 'PAAS'),
(3, 'FSM');



INSERT INTO UPDATESCOMPANY (AdminID, Ticker)
VALUES
(2, 'PAAS'),
(2, 'AG');



INSERT INTO UPDATESSTOCKPRICE (AdminID, Ticker, Date_Updated)
VALUES
(2, 'PAAS', '2024-03-01'),
(2, 'AG', '2024-03-01');



INSERT INTO UPDATESPRODUCTIONDATA (AdminID, Ticker, Period)
VALUES
(2, 'PAAS', 'Q4-2023'),
(2, 'AG', 'Q4-2023');
