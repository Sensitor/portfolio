public class Pretre extends Profil {
    public Pretre() {
        super("Pretre", 8);
    }

    @Override
    public int calculerPV(int modCon) {
        return 8 + modCon;
    }

    @Override
    public int getAttaqueMagique(int modInt, int modSag) {
        return modSag + 1;
    }
}
