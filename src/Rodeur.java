public class Rodeur extends Profil {
    public Rodeur() {
        super("Rodeur", 8, 8);
        voies.add(new VoieDeLArcher());
        voies.add(new VoieCompagnonAnimal());
        voies.add(new VoieDuTraqueur());
    }

    @Override
    public int getBonusAttaqueDistance(int niv) {
        return niv;
    }
}
