import java.util.ArrayList;
import java.util.List;

public abstract class Voie {
    private String nom;
    protected List<Competence> competences;

    public Voie(String nom) {
        this.nom = nom;
        this.competences = new ArrayList<>();
    }

    public String getNom() {
        return nom;
    }

    public List<Competence> getCompetences() {
        return competences;
    }

    public Competence getCompetence(int rang) {
        for (Competence c : competences) {
            if (c.getRang() == rang) {
                return c;
            }
        }
        return null;
    }

    public boolean peutAcquerir(Competence c, Personnage perso) {
        if (c.getRang() > perso.getNiveau()) {
            return false;
        }
        for (int r = 1; r < c.getRang(); r++) {
            Competence prereq = getCompetence(r);
            if (prereq != null && !perso.getCompetences().contains(prereq)) {
                return false;
            }
        }
        return true;
    }
}
