import java.util.ArrayList;
import java.util.List;

public class Personnage {
    private String nom;
    private int niveau;
    private int pointsCompetence;
    private Race race;
    private Profil profil;
    private Caracteristique force;
    private Caracteristique dexterite;
    private Caracteristique constitution;
    private Caracteristique intelligence;
    private Caracteristique sagesse;
    private Caracteristique charisme;
    private List<Competence> competences;
    private int pointsDeVie;

    public Personnage(String nom, Race race, Profil profil) {
        this.nom = nom;
        this.race = race;
        this.profil = profil;
        this.niveau = 1;
        this.pointsCompetence = 0;
        this.competences = new ArrayList<>();
        this.force = new Caracteristique(Des.lancer3d6());
        this.dexterite = new Caracteristique(Des.lancer3d6());
        this.constitution = new Caracteristique(Des.lancer3d6());
        this.intelligence = new Caracteristique(Des.lancer3d6());
        this.sagesse = new Caracteristique(Des.lancer3d6());
        this.charisme = new Caracteristique(Des.lancer3d6());
        race.appliquerModificateurs(this);
        this.pointsDeVie = profil.calculerPV(getMod(constitution.get()), 1);
    }

    public void levelUp(String... nomsCompetences) throws CompetenceException {
        int pointsDispo = 2;
        List<Competence> aAcquerir = new ArrayList<>();

        for (String nomComp : nomsCompetences) {
            Competence c = trouverCompetenceDansVoies(nomComp);
            if (c == null) {
                throw new CompetenceException("Competence inconnue : " + nomComp);
            }
            if (competences.contains(c)) {
                throw new CompetenceException("Competence deja acquise : " + nomComp);
            }
            aAcquerir.add(c);
        }

        int coutTotal = 0;
        for (Competence c : aAcquerir) {
            coutTotal += c.getCout();
        }
        if (coutTotal > pointsDispo) {
            throw new CompetenceException("Pas assez de points de competence (cout: " + coutTotal + ", dispo: " + pointsDispo + ")");
        }

        niveau++;

        for (Competence c : aAcquerir) {
            Voie voie = trouverVoieDeCompetence(c);
            if (voie == null || !voie.peutAcquerir(c, this)) {
                niveau--;
                throw new CompetenceException("Prerequis non remplis pour : " + c.getNom());
            }
        }

        competences.addAll(aAcquerir);
        pointsCompetence += pointsDispo - coutTotal;

        int pvGagnes = Des.lancer(profil.getDesVie()) + getMod(constitution.get()) + race.getBonusPVParNiveau();
        if (pvGagnes < 1) pvGagnes = 1;
        pointsDeVie += pvGagnes;
    }

    private Competence trouverCompetenceDansVoies(String nom) {
        for (Voie v : profil.getVoies()) {
            for (Competence c : v.getCompetences()) {
                if (c.getNom().equalsIgnoreCase(nom)) {
                    return c;
                }
            }
        }
        return null;
    }

    private Voie trouverVoieDeCompetence(Competence comp) {
        for (Voie v : profil.getVoies()) {
            if (v.getCompetences().contains(comp)) {
                return v;
            }
        }
        return null;
    }

    public int getMod(int carac) {
        return (carac / 2) - 5;
    }

    public int getDefense() {
        return 10 + getMod(dexterite.get());
    }

    public int getAttaqueMelee() {
        return getMod(force.get()) + 1 + profil.getBonusAttaqueMelee(niveau);
    }

    public int getAttaqueDistance() {
        return getMod(dexterite.get()) + 1 + profil.getBonusAttaqueDistance(niveau);
    }

    public int getPointsDeVie() {
        return pointsDeVie;
    }

    public int getAttaqueMagique() {
        return profil.getAttaqueMagique(getMod(intelligence.get()), getMod(sagesse.get()), niveau);
    }

    public void afficher() {
        System.out.println("=== " + nom + " (Niveau " + niveau + ") ===");
        System.out.println("Race : " + race.getNom());
        System.out.println("Profil : " + profil.getNom());
        System.out.println("Force : " + force.get() + " (mod " + getMod(force.get()) + ")");
        System.out.println("Dexterite : " + dexterite.get() + " (mod " + getMod(dexterite.get()) + ")");
        System.out.println("Constitution : " + constitution.get() + " (mod " + getMod(constitution.get()) + ")");
        System.out.println("Intelligence : " + intelligence.get() + " (mod " + getMod(intelligence.get()) + ")");
        System.out.println("Sagesse : " + sagesse.get() + " (mod " + getMod(sagesse.get()) + ")");
        System.out.println("Charisme : " + charisme.get() + " (mod " + getMod(charisme.get()) + ")");
        System.out.println("Points de vie : " + pointsDeVie);
        System.out.println("Defense : " + getDefense());
        System.out.println("Attaque melee : " + getAttaqueMelee());
        System.out.println("Attaque distance : " + getAttaqueDistance());
        if (getAttaqueMagique() > 0) {
            System.out.println("Attaque magique : " + getAttaqueMagique());
        }
        if (!competences.isEmpty()) {
            System.out.print("Competences : ");
            for (int i = 0; i < competences.size(); i++) {
                System.out.print(competences.get(i).getNom());
                if (i < competences.size() - 1) System.out.print(", ");
            }
            System.out.println();
        }
    }

    public int getNiveau() { return niveau; }
    public List<Competence> getCompetences() { return competences; }
    public Caracteristique getForce() { return force; }
    public Caracteristique getDexterite() { return dexterite; }
    public Caracteristique getConstitution() { return constitution; }
    public Caracteristique getIntelligence() { return intelligence; }
    public Caracteristique getSagesse() { return sagesse; }
    public Caracteristique getCharisme() { return charisme; }
}
