public class Personnage {
    private String nom;
    private Race race;
    private Profil profil;
    private Caracteristique force;
    private Caracteristique dexterite;
    private Caracteristique constitution;
    private Caracteristique intelligence;
    private Caracteristique sagesse;
    private Caracteristique charisme;

    public Personnage(String nom, Race race, Profil profil) {
        this.nom = nom;
        this.race = race;
        this.profil = profil;
        this.force = new Caracteristique(Des.lancer3d6());
        this.dexterite = new Caracteristique(Des.lancer3d6());
        this.constitution = new Caracteristique(Des.lancer3d6());
        this.intelligence = new Caracteristique(Des.lancer3d6());
        this.sagesse = new Caracteristique(Des.lancer3d6());
        this.charisme = new Caracteristique(Des.lancer3d6());
        race.appliquerModificateurs(this);
    }

    public int getMod(int carac) {
        return (carac / 2) - 5;
    }

    public int getDefense() {
        return 10 + getMod(dexterite.get());
    }

    public int getAttaqueMelee() {
        return getMod(force.get()) + 1;
    }

    public int getAttaqueDistance() {
        return getMod(dexterite.get()) + 1;
    }

    public int getPointsDeVie() {
        return profil.calculerPV(getMod(constitution.get()));
    }

    public int getAttaqueMagique() {
        return profil.getAttaqueMagique(getMod(intelligence.get()), getMod(sagesse.get()));
    }

    public void afficher() {
        System.out.println("=== " + nom + " ===");
        System.out.println("Race : " + race.getNom());
        System.out.println("Profil : " + profil.getNom());
        System.out.println("Force : " + force.get() + " (mod " + getMod(force.get()) + ")");
        System.out.println("Dexterite : " + dexterite.get() + " (mod " + getMod(dexterite.get()) + ")");
        System.out.println("Constitution : " + constitution.get() + " (mod " + getMod(constitution.get()) + ")");
        System.out.println("Intelligence : " + intelligence.get() + " (mod " + getMod(intelligence.get()) + ")");
        System.out.println("Sagesse : " + sagesse.get() + " (mod " + getMod(sagesse.get()) + ")");
        System.out.println("Charisme : " + charisme.get() + " (mod " + getMod(charisme.get()) + ")");
        System.out.println("Points de vie : " + getPointsDeVie());
        System.out.println("Defense : " + getDefense());
        System.out.println("Attaque melee : " + getAttaqueMelee());
        System.out.println("Attaque distance : " + getAttaqueDistance());
        System.out.println("Attaque magique : " + getAttaqueMagique());
    }

    public Caracteristique getForce() { return force; }
    public Caracteristique getDexterite() { return dexterite; }
    public Caracteristique getConstitution() { return constitution; }
    public Caracteristique getIntelligence() { return intelligence; }
    public Caracteristique getSagesse() { return sagesse; }
    public Caracteristique getCharisme() { return charisme; }
}
