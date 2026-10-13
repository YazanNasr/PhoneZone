DROP DATABASE IF EXISTS IEEE;
CREATE DATABASE IEEE;
USE IEEE;

CREATE TABLE Categories (
    CategoryID INT AUTO_INCREMENT PRIMARY KEY,
    CategoryName VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE Products (
    ProductID INT AUTO_INCREMENT PRIMARY KEY,
    ProductName VARCHAR(100) NOT NULL,
    Brand VARCHAR(50) NOT NULL,
    Description TEXT NOT NULL,
    Price DECIMAL(10,2) NOT NULL,
    Stock INT NOT NULL,
    Image VARCHAR(100) NOT NULL,
    Rating DECIMAL(2,1) DEFAULT 4.5,
    CategoryID INT NOT NULL,

    CONSTRAINT chk_price CHECK (Price >= 0),
    CONSTRAINT chk_stock CHECK (Stock >= 0),
    CONSTRAINT chk_rating CHECK (Rating >= 0 AND Rating <= 5),

    FOREIGN KEY (CategoryID)
        REFERENCES Categories(CategoryID)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

INSERT INTO Categories (CategoryName)
VALUES
('Apple'),
('Samsung'),
('Google');

INSERT INTO Products
(ProductName, Brand, Description, Price, Stock, Image, Rating, CategoryID)
VALUES
(
'iPhone 15 Pro',
'Apple',
'Premium Apple smartphone with titanium design, A17 Pro chip, USB-C charging, and a pro camera system.',
999.99,
8,
'ip15.png',
4.8,
1
),
(
'Samsung Galaxy S24',
'Samsung',
'Flagship Samsung smartphone with Galaxy AI features, AMOLED display, fast performance, and advanced camera system.',
899.99,
6,
's24.jpg',
4.9,
2
),
(
'Google Pixel 8',
'Google',
'Google AI smartphone with clean Android experience, Tensor G3 chip, excellent camera features, and all-day battery life.',
699.99,
10,
'gp8.jpeg',
4.7,
3
);

SELECT 
    p.ProductID,
    p.ProductName,
    p.Brand,
    p.Description,
    p.Price,
    p.Stock,
    p.Image,
    p.Rating,
    c.CategoryName
FROM Products p
JOIN Categories c
ON p.CategoryID = c.CategoryID;
SELECT ProductID, ProductName, Stock
FROM Products;