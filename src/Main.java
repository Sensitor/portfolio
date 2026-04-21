public class Main {
    public static void main(String[] args) {

        Personnage guerrier = new Personnage("Thorin", new Nain(), new Guerrier());
        guerrier.afficher();

        try {
            guerrier.levelUp("Vivacite", "Robustesse");
            System.out.println("\n--- Apres level up ---");
            guerrier.afficher();
        } catch (CompetenceException e) {
            System.out.println("Erreur: " + e.getMessage());
        }

        try {
            guerrier.levelUp("Desarmer", "Armure naturelle");
            System.out.println("\n--- Apres level up 2 ---");
            guerrier.afficher();
        } catch (CompetenceException e) {
            System.out.println("Erreur: " + e.getMessage());
        }

        System.out.println("\n==============================\n");

        Personnage mage = new Personnage("Elyndra", new Elfe(), new Magicien());
        mage.afficher();

        try {
            mage.levelUp("Projectile magique", "Armure du mage");
            System.out.println("\n--- Apres level up ---");
            mage.afficher();
        } catch (CompetenceException e) {
            System.out.println("Erreur: " + e.getMessage());
        }

        System.out.println("\n==============================\n");

        Personnage voleur = new Personnage("Shadow", new Halfelin(), new Voleur());
        voleur.afficher();

        try {
            voleur.levelUp("Discretion", "Esquive");
            System.out.println("\n--- Apres level up ---");
            voleur.afficher();
        } catch (CompetenceException e) {
            System.out.println("Erreur: " + e.getMessage());
        }

        System.out.println("\n==============================\n");

        // Test d'une erreur : competence rang 3 sans avoir rang 1 et 2
        Personnage barbare = new Personnage("Gruk", new DemiOrque(), new Barbare());
        barbare.afficher();

        try {
            barbare.levelUp("Double attaque");
            System.out.println("Ceci ne devrait pas s'afficher");
        } catch (CompetenceException e) {
            System.out.println("\nException attrapee : " + e.getMessage());
        }
    }
}
