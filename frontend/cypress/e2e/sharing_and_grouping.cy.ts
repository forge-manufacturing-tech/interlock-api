describe('Sharing and Grouping', () => {
  const userA = {
    name: 'User A ' + Math.random().toString(36).substring(7),
    email: `user_a_${Math.random().toString(36).substring(7)}@example.com`,
    password: 'password123'
  };
  const userB = {
    name: 'User B ' + Math.random().toString(36).substring(7),
    email: `user_b_${Math.random().toString(36).substring(7)}@example.com`,
    password: 'password123'
  };

  it('should allow grouping by project label and sharing with other users', () => {
    // 1. Signup User B first (so they exist for sharing)
    cy.visit('/signup');
    cy.get('input[placeholder="Your name"]').type(userB.name);
    cy.get('input[placeholder="you@example.com"]').type(userB.email);
    cy.get('input[placeholder="Min 6 characters"]').type(userB.password);
    cy.get('input[placeholder="Repeat your password"]').type(userB.password);
    cy.get('button').contains('CREATE ACCOUNT').click();
    cy.url().should('include', '/dashboard', { timeout: 20000 });
    cy.contains('button', 'Logout', { timeout: 10000 }).click();

    // 2. Signup User A
    cy.visit('/signup');
    cy.get('input[placeholder="Your name"]').type(userA.name);
    cy.get('input[placeholder="you@example.com"]').type(userA.email);
    cy.get('input[placeholder="Min 6 characters"]').type(userA.password);
    cy.get('input[placeholder="Repeat your password"]').type(userA.password);
    cy.get('button').contains('CREATE ACCOUNT').click();
    cy.url().should('include', '/dashboard', { timeout: 20000 });

    // 3. Create a part with a project label and cost
    cy.contains('button', 'New Part').click();
    cy.get('input[placeholder="e.g. 6061 Aluminum Plate"]').type('Cypress Test Part');
    cy.get('input[type="number"]').first().clear().type('10.50'); // Set cost
    cy.get('input[placeholder="e.g. Project X"]').type('Cypress Project');
    cy.get('button').contains('CREATE MATERIAL').click();

    // 4. Verify grouping
    // UI uses text-transform: uppercase for headers
    cy.contains('h2', /CYPRESS PROJECT/i, { timeout: 15000 }).should('be.visible');
    cy.contains('Cypress Test Part').should('be.visible');

    // 5. Share with User B
    cy.contains('Cypress Test Part').click();
    cy.contains(/SHARING/i, { timeout: 10000 }).should('be.visible');
    // Find User B in the list and click
    cy.contains('button', userB.name, { timeout: 10000 }).scrollIntoView().click();

    // 6. Verify Private badge
    cy.contains('span', 'Private', { timeout: 5000 }).should('be.visible');

    // 7. Logout User A and Login as User B
    cy.contains('button', 'Logout').click();
    cy.visit('/login');
    cy.get('input[placeholder="you@example.com"]').type(userB.email);
    cy.get('input[type="password"]').type(userB.password);
    cy.get('button').contains('SIGN IN').click();
    cy.url().should('include', '/dashboard', { timeout: 20000 });

    // 8. Verify User B can see shared part
    cy.contains('Cypress Test Part', { timeout: 15000 }).should('be.visible');
  });
});
