/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
 
/**
 * Represents a type of labor (e.g. 'Welding', 'Assembly').
 *
 * ``hourly_rate`` is the cost per hour for this labor type.
 * ``skill_level`` documents the required skill or certification
 * (e.g. "AWS D1.1 Certified Welder") — essential for work instructions.
 */
export type LaborNode = {
    id?: string;
    name?: (string | null);
    description?: (string | null);
    hourly_rate?: number;
    skill_level?: (string | null);
};

