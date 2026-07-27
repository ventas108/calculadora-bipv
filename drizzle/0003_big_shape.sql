CREATE TABLE `bipv_hourly_results` (
	`id` int AUTO_INCREMENT NOT NULL,
	`simulationId` int NOT NULL,
	`month` int NOT NULL,
	`hourlyData` json NOT NULL,
	`monthlySummary` json NOT NULL,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `bipv_hourly_results_id` PRIMARY KEY(`id`)
);
