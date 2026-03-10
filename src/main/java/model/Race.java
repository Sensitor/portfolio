package model;

/**
 * Enum représentant les différentes races disponibles pour un personnage.
 *
 * Chaque race possède des bonus/malus sur les caractéristiques :
 * - Humain     : aucun bonus ni malus
 * - Elfe       : Dex+2, For-2
 * - Demi-Elfe  : aucun bonus ni malus
 * - Nain       : Con+2, Dex-2
 * - Demi-Orque : For+2, Int-2, Cha-2
 */
public enum Race {

    HUMAIN("Humain", 0, 0, 0, 0, 0, 0),
    ELFE("Elfe", -2, 2, 0, 0, 0, 0),
    DEMI_ELFE("Demi-Elfe", 0, 0, 0, 0, 0, 0),
    NAIN("Nain", 0, -2, 2, 0, 0, 0),
    DEMI_ORQUE("Demi-Orque", 2, 0, 0, -2, 0, -2);

    private final String nom;
    private final int bonusForce;
    private final int bonusDexterite;
    private final int bonusConstitution;
    private final int bonusIntelligence;
    private final int bonusSagesse;
    private final int bonusCharisme;

    /**
     * Constructeur de l'enum Race.
     * Les bonus peuvent être positifs (bonus) ou négatifs (malus).
     */
    Race(String nom, int bonusForce, int bonusDexterite, int bonusConstitution,
         int bonusIntelligence, int bonusSagesse, int bonusCharisme) {
        this.nom = nom;
        this.bonusForce = bonusForce;
        this.bonusDexterite = bonusDexterite;
        this.bonusConstitution = bonusConstitution;
        this.bonusIntelligence = bonusIntelligence;
        this.bonusSagesse = bonusSagesse;
        this.bonusCharisme = bonusCharisme;
    }

    // --- Getters ---

    public String getNom() { return nom; }
    public int getBonusForce() { return bonusForce; }
    public int getBonusDexterite() { return bonusDexterite; }
    public int getBonusConstitution() { return bonusConstitution; }
    public int getBonusIntelligence() { return bonusIntelligence; }
    public int getBonusSagesse() { return bonusSagesse; }
    public int getBonusCharisme() { return bonusCharisme; }

    @Override
    public String toString() {
        return nom;
    }
}
