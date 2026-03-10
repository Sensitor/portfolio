package utils;

import java.util.Random;

/**
 * Classe utilitaire pour simuler des lancers de dés.
 * Utilisée pour générer les caractéristiques des personnages (3d6).
 */
public class Des {

    private static final Random random = new Random();

    /**
     * Lance un dé à 6 faces.
     * @return un entier entre 1 et 6
     */
    public static int lancerD6() {
        return random.nextInt(6) + 1;
    }

    /**
     * Lance 3 dés à 6 faces et retourne la somme.
     * Utilisé pour générer une caractéristique (résultat entre 3 et 18).
     * @return la somme de 3d6
     */
    public static int lancer3D6() {
        return lancerD6() + lancerD6() + lancerD6();
    }
}
