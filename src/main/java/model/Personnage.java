package model;

import utils.Des;

/**
 * Classe principale représentant un personnage de jeu de rôle.
 *
 * Un personnage possède :
 * - Un nom
 * - Une race (qui applique des bonus/malus aux caractéristiques)
 * - Un profil (qui détermine les PV et éventuellement l'attaque magique)
 * - 6 caractéristiques générées aléatoirement (3d6) : Force, Dextérité,
 *   Constitution, Intelligence, Sagesse, Charisme
 *
 * Les valeurs dérivées sont calculées automatiquement :
 * - Modificateur = (Caractéristique / 2) - 5
 * - Points de vie = pvBase du profil + Mod Constitution
 * - Défense = 10 + Mod Dextérité
 * - Attaque mêlée = Mod Force + 1
 * - Attaque distance = Mod Dextérité + 1
 * - Attaque magique (si applicable) = Mod de la carac magique + 1
 */
public class Personnage {

    // --- Attributs ---
    private String nom;
    private Race race;
    private Profil profil;

    // Caractéristiques de base (après application des bonus raciaux)
    private int force;
    private int dexterite;
    private int constitution;
    private int intelligence;
    private int sagesse;
    private int charisme;

    // Valeurs dérivées
    private int pointsDeVie;
    private int defense;
    private int attaqueMelee;
    private int attaqueDistance;
    private int attaqueMagique;

    // --- Constructeur ---

    /**
     * Crée un personnage avec un nom, une race et un profil.
     * Les caractéristiques sont générées aléatoirement (3d6)
     * puis modifiées par les bonus raciaux.
     *
     * @param nom    le nom du personnage
     * @param race   la race choisie
     * @param profil le profil (classe) choisi
     */
    public Personnage(String nom, Race race, Profil profil) {
        this.nom = nom;
        this.race = race;
        this.profil = profil;

        // Générer les caractéristiques de base (3d6) + bonus raciaux
        genererCaracteristiques();

        // Calculer les valeurs dérivées
        calculerValeursDerivees();
    }

    // --- Méthodes privées ---

    /**
     * Génère les 6 caractéristiques via 3d6 et applique les bonus raciaux.
     * Une caractéristique ne peut pas descendre en dessous de 1.
     */
    private void genererCaracteristiques() {
        this.force = Math.max(1, Des.lancer3D6() + race.getBonusForce());
        this.dexterite = Math.max(1, Des.lancer3D6() + race.getBonusDexterite());
        this.constitution = Math.max(1, Des.lancer3D6() + race.getBonusConstitution());
        this.intelligence = Math.max(1, Des.lancer3D6() + race.getBonusIntelligence());
        this.sagesse = Math.max(1, Des.lancer3D6() + race.getBonusSagesse());
        this.charisme = Math.max(1, Des.lancer3D6() + race.getBonusCharisme());
    }

    /**
     * Calcule toutes les valeurs dérivées à partir des caractéristiques.
     */
    private void calculerValeursDerivees() {
        // Points de vie = PV de base du profil + modificateur de Constitution
        this.pointsDeVie = Math.max(1, profil.getPvBase() + getModificateur(constitution));

        // Défense = 10 + modificateur de Dextérité
        this.defense = 10 + getModificateur(dexterite);

        // Attaque mêlée = modificateur de Force + 1
        this.attaqueMelee = getModificateur(force) + 1;

        // Attaque distance = modificateur de Dextérité + 1
        this.attaqueDistance = getModificateur(dexterite) + 1;

        // Attaque magique (seulement pour Magicien et Prêtre)
        if (profil.isPossedeMagie()) {
            int caracMagique = getCaracteristiqueMagique();
            this.attaqueMagique = getModificateur(caracMagique) + 1;
        } else {
            this.attaqueMagique = 0;
        }
    }

    /**
     * Retourne la valeur de la caractéristique utilisée pour la magie,
     * selon le profil du personnage.
     */
    private int getCaracteristiqueMagique() {
        switch (profil.getCaracMagie()) {
            case "Intelligence":
                return intelligence;
            case "Sagesse":
                return sagesse;
            default:
                return 0;
        }
    }

    // --- Méthodes publiques ---

    /**
     * Calcule le modificateur d'une caractéristique.
     * Formule : Mod = (Caractéristique / 2) - 5
     *
     * @param caracteristique la valeur de la caractéristique
     * @return le modificateur (peut être négatif)
     */
    public static int getModificateur(int caracteristique) {
        return (caracteristique / 2) - 5;
    }

    /**
     * Affiche la fiche complète du personnage.
     */
    public void afficherFiche() {
        System.out.println("========================================");
        System.out.println("  FICHE DE PERSONNAGE");
        System.out.println("========================================");
        System.out.println("  Nom    : " + nom);
        System.out.println("  Race   : " + race.getNom());
        System.out.println("  Profil : " + profil.getNom());
        System.out.println("----------------------------------------");
        System.out.println("  CARACTERISTIQUES");
        System.out.println("----------------------------------------");
        afficherCaracteristique("Force", force);
        afficherCaracteristique("Dextérité", dexterite);
        afficherCaracteristique("Constitution", constitution);
        afficherCaracteristique("Intelligence", intelligence);
        afficherCaracteristique("Sagesse", sagesse);
        afficherCaracteristique("Charisme", charisme);
        System.out.println("----------------------------------------");
        System.out.println("  COMBAT");
        System.out.println("----------------------------------------");
        System.out.println("  Points de vie    : " + pointsDeVie);
        System.out.println("  Défense          : " + defense);
        System.out.println("  Attaque mêlée    : " + attaqueMelee);
        System.out.println("  Attaque distance  : " + attaqueDistance);
        if (profil.isPossedeMagie()) {
            System.out.println("  Attaque magique  : " + attaqueMagique
                    + " (" + profil.getCaracMagie() + ")");
        }
        System.out.println("========================================\n");
    }

    /**
     * Affiche une caractéristique avec son modificateur formaté.
     */
    private void afficherCaracteristique(String nomCarac, int valeur) {
        int mod = getModificateur(valeur);
        String signe = mod >= 0 ? "+" : "";
        System.out.printf("  %-15s : %2d  (mod %s%d)%n", nomCarac, valeur, signe, mod);
    }

    // --- Getters ---

    public String getNom() { return nom; }
    public Race getRace() { return race; }
    public Profil getProfil() { return profil; }
    public int getForce() { return force; }
    public int getDexterite() { return dexterite; }
    public int getConstitution() { return constitution; }
    public int getIntelligence() { return intelligence; }
    public int getSagesse() { return sagesse; }
    public int getCharisme() { return charisme; }
    public int getPointsDeVie() { return pointsDeVie; }
    public int getDefense() { return defense; }
    public int getAttaqueMelee() { return attaqueMelee; }
    public int getAttaqueDistance() { return attaqueDistance; }
    public int getAttaqueMagique() { return attaqueMagique; }

    // --- Setters ---

    public void setNom(String nom) { this.nom = nom; }
}
