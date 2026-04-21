import java.util.ArrayList;
import java.util.List;

public abstract class Profil {
    private String nom;
    protected int pvBase;
    protected int desVie;
    protected List<Voie> voies;

    public Profil(String nom, int pvBase, int desVie) {
        this.nom = nom;
        this.pvBase = pvBase;
        this.desVie = desVie;
        this.voies = new ArrayList<>();
    }

    public int calculerPV(int modCon, int niv) {
        int pv = pvBase + modCon;
        for (int i = 2; i <= niv; i++) {
            pv += Des.lancer(desVie) + modCon;
        }
        return pv;
    }

    public int getAttaqueMagique(int modInt, int modSag, int niv) {
        return 0;
    }

    public int getBonusAttaqueMelee(int niv) {
        return 0;
    }

    public int getBonusAttaqueDistance(int niv) {
        return 0;
    }

    public List<Voie> getVoies() {
        return voies;
    }

    public int getDesVie() {
        return desVie;
    }

    public String getNom() {
        return nom;
    }
}
