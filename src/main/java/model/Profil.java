package model;

/**
 * Enum représentant les profils (classes) disponibles pour un personnage.
 *
 * Chaque profil définit :
 * - Les points de vie de base (PV = pvBase + Mod Constitution)
 * - Si le profil possède une attaque magique
 * - Quelle caractéristique est utilisée pour l'attaque magique
 *
 * Formules des PV :
 * - Guerrier : 10 + Mod Con
 * - Magicien :  4 + Mod Con  (attaque magique = Mod Int + 1)
 * - Prêtre   :  8 + Mod Con  (attaque magique = Mod Sag + 1)
 * - Rôdeur   :  8 + Mod Con
 * - Voleur   :  6 + Mod Con
 */
public enum Profil {

    GUERRIER("Guerrier", 10, false, ""),
    MAGICIEN("Magicien", 4, true, "Intelligence"),
    PRETRE("Prêtre", 8, true, "Sagesse"),
    RODEUR("Rôdeur", 8, false, ""),
    VOLEUR("Voleur", 6, false, "");

    private final String nom;
    private final int pvBase;
    private final boolean possedeMagie;
    private final String caracMagie; // caractéristique utilisée pour l'attaque magique

    Profil(String nom, int pvBase, boolean possedeMagie, String caracMagie) {
        this.nom = nom;
        this.pvBase = pvBase;
        this.possedeMagie = possedeMagie;
        this.caracMagie = caracMagie;
    }

    // --- Getters ---

    public String getNom() { return nom; }
    public int getPvBase() { return pvBase; }
    public boolean isPossedeMagie() { return possedeMagie; }
    public String getCaracMagie() { return caracMagie; }

    @Override
    public String toString() {
        return nom;
    }
}
