public abstract class Profil {
    private String nom;
    protected int pvBase;

    public Profil(String nom, int pvBase) {
        this.nom = nom;
        this.pvBase = pvBase;
    }

    public int calculerPV(int modCon) {
        return pvBase + modCon;
    }

    public int getAttaqueMagique(int modInt, int modSag) {
        return 0;
    }

    public String getNom() {
        return nom;
    }
}
